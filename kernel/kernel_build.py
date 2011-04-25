#!/usr/bin/python
# ezGingerbread Kernel build script

"""
This script is to aid in generating the ebi0, ebi1, 2708 kernels for
ezGingerbread Dream/Sapphire, such as the pre-built ones.

Please note this script is to be run from the android root as:
device/htc/dream-sapphire/kernel/kernel_build.py

*****************************************************

To re-generate the files in this directory:

Initial build (or clean build where we re-fetch the kernel code):

#get the kernel source
device/htc/dream-sapphire/kernel/kernel_build.py fetch
#build the kernel
device/htc/dream-sapphire/kernel/kernel_build.py build

Update build (where you want a clean build but don't want to re-fetch all of
              the kernel source via git):

#clean the current build
device/htc/dream-sapphire/kernel/kernel_build.py clean
#sync the kernel source
device/htc/dream-sapphire/kernel/kernel_build.py sync
#build
device/htc/dream-sapphire/kernel/kernel_build.py build

******************************************************

Note: this is only designed to run on Linux boxes and may need modifications
to operate on other operating systems.

You will also need to have installed the squashfs, and lzma packages for this to operate correctly.
"""

import sys
import os
import os.path
import shutil
import re

toolchain_path='prebuilt/linux-x86/toolchain/arm-eabi-4.4.3/bin'
gitremote='https://github.com/ezterry/kernel-biff-testing.git'
workdir='ezgb-kernel'
configtmpl='ezgb_%s_defconfig'

srcdir =os.path.join(workdir,'src')
vebi0dir = os.path.join(workdir,'ebi0')
vebi1dir = os.path.join(workdir,'ebi1')
v2708dir = os.path.join(workdir,'2708')

def rmtree(path):
    """remove a tree if it exists, else do nothing"""
    if(os.path.isdir(path)):
        shutil.rmtree(path)

def read_version(workdir):
    """read the version magic out of the wlan.ko module
       and return the version string"""
    val="unknown-1"
    fp=open(os.path.join(workdir,'drivers/net/wireless/tiwlan1251/wlan.ko'),
            'rb')
    blob = fp.read()
    fp.close()
    m=re.search('\0vermagic=([0-9]\.[^\0]+)\0',blob)
    if(m is not None):
        print("Kernel version magic: " + m.group(1))
        m=re.match('(\S+)',m.group(1))
    if(m is not None):
        val = m.group(1)
    return(val)

def runbuild(outpath,cfg):
    """Run the build with destination outpath, using cfg"""
    cpucnt=1
    outpath=os.path.join(os.getcwd(),outpath)
    gccpath=os.path.join(os.getcwd(),toolchain_path)
    
    if(os.path.isfile('/proc/cpuinfo')):
        data = open('/proc/cpuinfo','r').read()
        try:
            cpucnt=int(re.search('cpu cores\s+:\s+([0-9]+)',data).group(1))
        except:
            pass #cpucnt assumed 1
    
    #make output dir if needed
    if(not os.path.isdir(outpath)):
        os.mkdir(outpath)
    
    #remove the zImage if it exists:
    if(os.path.isfile(os.path.join(outpath,'arch/arm/boot/zImage'))):
        os.unlink(os.path.join(outpath,'arch/arm/boot/zImage'))

    #internal build script (we will let make determine what is clean or not
    os.system("sh -c '(" +
              " cd " + srcdir + "; " +
              #prepare enviroment
              " export PATH=\"" + gccpath + "\":$PATH; " +
              " export ARCH=arm; " +
              " export CROSS_COMPILE=arm-eabi-; " + 
              " export KERNEL_DIR=`pwd`; " +
              #generate cfg from template
              " make " + cfg + " O=\"" + outpath + "\";" +
              #build the kernel
              " make -j " + str(cpucnt+1) + " O=\"" + outpath + "\";" +
              #"install" modules to outpath/build dir
              " make modules_install O=\"" + outpath + "\" " + 
                  "INSTALL_MOD_PATH=\"" + os.path.join(outpath,"build") + 
                  "\";" +
              ")'")
    kvers = read_version(outpath)
    buildlink = os.path.join(outpath,'build/lib/modules',kvers,'build')
    sourcelink = os.path.join(outpath,'build/lib/modules',kvers,'source')
    
    #remove symlinks
    if(os.path.islink(buildlink)):
        os.unlink(buildlink)
    if(os.path.islink(sourcelink)):
        os.unlink(sourcelink)
    
    #make sure we have a kernel binary
    if(not os.path.isfile(os.path.join(outpath,'arch/arm/boot/zImage'))):
        print("ERROR: zImage missing [" + cfg + "]")
        sys.exit(-1)

    #move wlan.ko
    if(not os.path.isfile(os.path.join(outpath,'build/lib/modules',kvers,
                      'kernel/drivers/net/wireless/tiwlan1251/wlan.ko'))):
        print("ERROR: wlan.ko missing [" + cfg + "]")
        sys.exit(-1)

    os.renames(os.path.join(outpath,'build/lib/modules',kvers,
                            'kernel/drivers/net/wireless/tiwlan1251/wlan.ko'),
               os.path.join(outpath,'build/lib/modules/wlan.ko'))

    #make squashfs
    os.system("sh -c \'(" + 
              "cd \"" + os.path.join(outpath,'build/lib/modules') + "\";" +
              #strip down the kernel modules
              "find ./ -name \"*.ko\" -print0 | xargs -0 \"" +
                 os.path.join(gccpath,'arm-eabi-strip') + "\" " +
                 "--strip-unneeded; " +
              #add to squashfs
              "mksquashfs wlan.ko \"" + kvers + "\" " + 
                 "modules.sqf -all-root -noappend;)\'")

    print("build of " + cfg + " complete..")

def copyKernelFiles():
    """Copy the new kernel files into place"""
    dskernel='device/htc/dream-sapphire/kernel'
    
    #delete existing files
    for filename in ( '2708-modules.sqf' ,
                      '2708-zImage' ,
                      'ebi0-modules.sqf' ,
                      'ebi0-zImage' ,
                      'ebi1-modules.sqf' ,
                      'ebi1-zImage' ):
        if(os.path.isfile(os.path.join(dskernel,filename))):
            os.unlink(os.path.join(dskernel,filename))

    #copy the new files
    shutil.copyfile(os.path.join(v2708dir,'arch/arm/boot/zImage'),
                    os.path.join(dskernel,'2708-zImage'))
    shutil.copyfile(os.path.join(v2708dir,'build/lib/modules/modules.sqf'),
                    os.path.join(dskernel,'2708-modules.sqf'))
    shutil.copyfile(os.path.join(vebi0dir,'arch/arm/boot/zImage'),
                    os.path.join(dskernel,'ebi0-zImage'))
    shutil.copyfile(os.path.join(vebi0dir,'build/lib/modules/modules.sqf'),
                    os.path.join(dskernel,'ebi0-modules.sqf'))
    shutil.copyfile(os.path.join(vebi1dir,'arch/arm/boot/zImage'),
                    os.path.join(dskernel,'ebi1-zImage'))
    shutil.copyfile(os.path.join(vebi1dir,'build/lib/modules/modules.sqf'),
                    os.path.join(dskernel,'ebi1-modules.sqf'))

def main():
    """entry point"""
    if(not os.path.isdir(toolchain_path)):
        print("Please run this script from the android build root: ")
        print("> device/htc/dream-sapphire/kernel/kernel_build.py")
        return
    
    #we appear to be running properly
    if(len(sys.argv) > 1):
        action = sys.argv[1]
    else:
        action = 'help'

    if(action == "--help"):
        action = 'help'

    if(action == "fetch"):
        #fetch a clean copy of the git repo
        rmtree(workdir)
        os.mkdir(workdir)
        os.system('sh -c \'(cd ' + workdir + ';git clone ' + 
                  gitremote + ' src)\'')

    elif(action == "sync"):
        #attempts to sync the local repo (git pull)
        if(os.path.isdir(srcdir)):
            os.system('sh -c \'(cd ' + srcdir +
                      ';git pull origin)\'')
        else:
            print("Git repo not found, please run fetch to re-initialize")

    elif(action == "clean"):
        #purge the build dirs for a clean build
        rmtree(vebi0dir)
        rmtree(vebi1dir)
        rmtree(v2708dir)
        print("Clean")

    elif(action == "build"):
        #build all three kernels
        if(not os.path.isdir(srcdir)):
            rmtree(workdir)
            os.mkdir(workdir)
            os.system('sh -c \'(cd ' + workdir + ';git clone ' + 
                      gitremote + ' src)\'')
        #ok we can continue with the build 
        runbuild(vebi0dir,configtmpl % ('ebi0'))
        runbuild(vebi1dir,configtmpl % ('ebi1'))
        runbuild(v2708dir,configtmpl % ('2708'))
        copyKernelFiles()
        
    elif(action == "help"):
        #provide help string
        print("> device/htc/dream-sapphire/kernel/kernel_build.py <action>")
        print(" ")
        print("Actions:")
        print(" fetch: remove any existing git kernel repo and clone a new one")
        print(" sync: 'git pull origin' on the git kernel repo to sync it")
        print(" clean: remove the work build dirs for a clean kernel build")
        print(" build: if repo is missing fetch it, otherwise just build the" +
              "kernels")
        print(" help: This message")
        print(" ")
        print("To build a clean initial kernel only 'build' is needed, to make")
        print("a clean refresh run sync, clean, then build")
    else:
        print("Unknown action " + action + "!")

if __name__ == "__main__":
    main()

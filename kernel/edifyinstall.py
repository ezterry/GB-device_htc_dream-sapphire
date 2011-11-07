#!/usr/bin/python
"""
This is a special python module that will be exec'd
when it is time to install the kernel loading code
into the edify script

Here is where we implement the Anykernel functionality.
The build system will make the 2708+ kernel the primary
here we need to make patches for the ebi0/ebi1 kernels 
against the 2708 base; and inject the patches and logic 
into the update.zip
"""

#
# Copyright (C) 2011 ezterry3@gmail.com 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Note two modules are preloaded into global space
# common (build/tools/releasetools/common.py)
# edify_generator (build/tools/releasetools/edify_generator.py)
#
# We must implement a function of the following template
# make_boot_install(script,boot_img,input_zip,output_zip)
#
# This will be called when it it time to update the edify script in script

import os
import os.path
import tempfile
import shutil


def IsSymlink(info):
    """Return true if the zipfile.ZipInfo object passed in represents a
       symlink."""
    # as defined in build/tools/releasetools/ota_from_target_files
    return (info.external_attr >> 16) == 0120777

def unzip_boot_files(input_zip,output_path):
    files=filter(lambda f: f[:4]=='BOOT',input_zip.namelist())
    for f in files:
        outfile=os.path.join(output_path,f[4+len(os.path.sep):])
        
        #check the dir exists
        outdir =os.path.dirname(outfile)
        if(not os.path.isdir(outdir)):
            os.makedirs(outdir)
        #extract the file
        if(os.path.basename(outfile) != ""):
            if(IsSymlink(input_zip.getinfo(f))):
                #we have a symlink
                os.symlink(input_zip.read(f),outfile)
            else:
                #just create the output file
                fp=open(outfile,'wb')
                fp.write(input_zip.read(f))
                fp.close()

def generate_checksys(output_zip):
    checksys  = \
"""#!/sbin/sh
#
# Find system information based on the kernel command line and populate 
# nfo.prop

baseband=`awk '{m=match($0,/androidboot.baseband=([0-9a-zA-Z\.]*)/) ; print(substr($0,RSTART+21,RLENGTH-21))}' < /proc/cmdline`
bootloader=`awk '{m=match($0,/androidboot.bootloader=([0-9a-zA-Z\.]*)/) ; print(substr($0,RSTART+23,RLENGTH-23))}' < /proc/cmdline`
radioseries=`echo $baseband | awk '{print(substr($0,0,4))}'`
custommtd=`awk '/mtdparts/ {print("CustomMTD")}' < /proc/cmdline`
smisize=`awk '{m=match($0,/smisize=([0-9a-zA-Z\.]*)/) ; print(substr($0,RSTART+8,RLENGTH-8))}' < /proc/cmdline`
board=`cat /proc/cpuinfo  | grep Hardware | awk '{print $3}'`

#write out a prop file for the updater script to read
echo "baseband=$baseband" > /tmp/nfo.prop
echo "bootloader=$bootloader" >> /tmp/nfo.prop
echo "radioseries=$radioseries" >> /tmp/nfo.prop
echo "custommtd=$custommtd" >> /tmp/nfo.prop
echo "smisize=$smisize" >> /tmp/nfo.prop
echo "sysboard=$board" >> /tmp/nfo.prop
"""
    common.ZipWriteStr(output_zip,"checksys.sh",checksys)

def generate_firstboot(output_zip):
    firstboot = \
"""#!/system/xbin/sh
LOGINFO='log -p i -t firstboot '

$LOGINFO "Firstboot: cleanup process"
if [ -e /data/dalvik-cache ]
then
    $LOGINFO "Clear /data/dalvik-cache"
    busybox rm -rf /data/dalvik-cache/*
fi
if [ -e /cache/dalvik-cache ]
then
    $LOGINFO "Clear /cache/dalvik-cache"
    busybox rm -rf /cache/dalvik-cache/*
fi
if [ -e /sd-ext/dalvik-cache ]
then
    $LOGINFO "Clear /sd-ext/dalvik-cache"
    busybox rm -rf /sd-ext/dalvik-cache/*
fi
if [ -e /data/tombstones ]
then
    $LOGINFO "Clear historic tombstones"
    busybox rm -rf /data/tombstones/*
fi
if [ -e /data/data/com.android.vending/databases/market_assets.db ]
then
    $LOGINFO "Cleaning Market Superuser"
    sqlite3 /data/data/com.android.vending/databases/market_assets.db "delete from asset_versions WHERE package='com.noshufou.android.su'"
fi
$LOGINFO "Firstboot cleanup done"
"""
    common.ZipWriteStr(output_zip,"firstboot.sh",firstboot)

def make_boot_install(script,boot_img,input_zip,output_zip):
    android_root=os.getenv("ANDROID_BUILD_TOP")
    temp_root=tempfile.mkdtemp(suffix="autokernel")
    
    #the "base" file is the 2708 boot.img
    common.ZipWriteStr(output_zip,"kernel/2708-boot.img",boot_img.data)
    
    #GENERATE EBI0 boot.img
    unzip_boot_files(input_zip,os.path.join(temp_root,"ebi0_BOOT"))
    shutil.copy( os.path.join(android_root,
                   "device","htc","dream-sapphire","kernel","ebi0-zImage"),
                 os.path.join(temp_root,"ebi0_BOOT","kernel"))
    
    fp=open(os.path.join(temp_root,"ebi0_BOOT","base"),'w')
    fp.write("0x10000000")
    fp.close()

    ebi0_boot_img = common.File("ebi0_boot.img",
                       common.BuildBootableImage(
                         os.path.join(temp_root,"ebi0_BOOT")))
    
    common.ZipWriteStr(output_zip,"kernel/ebi0-boot.img",ebi0_boot_img.data)

    #GENERATE EBI1 boot.img
    unzip_boot_files(input_zip,os.path.join(temp_root,"ebi1_BOOT"))
    shutil.copy( os.path.join(android_root,
                   "device","htc","dream-sapphire","kernel","ebi1-zImage"),
                 os.path.join(temp_root,"ebi1_BOOT","kernel"))
    
    fp=open(os.path.join(temp_root,"ebi1_BOOT","base"),'w')
    fp.write("0x19200000")
    fp.close()

    ebi1_boot_img = common.File("ebi1_boot.img",
                       common.BuildBootableImage(
                         os.path.join(temp_root,"ebi1_BOOT")))
    
    common.ZipWriteStr(output_zip,"kernel/ebi1-boot.img",ebi1_boot_img.data)
    
    #copy in modules.sqf
    fp=open(os.path.join(android_root,
              "device","htc","dream-sapphire","kernel","ebi0-modules.sqf"),
              "rb")
    common.ZipWriteStr(output_zip,"kernel/ebi0-modules.sqf",fp.read())
    fp.close()

    fp=open(os.path.join(android_root,
              "device","htc","dream-sapphire","kernel","ebi1-modules.sqf"),
              "rb")
    common.ZipWriteStr(output_zip,"kernel/ebi1-modules.sqf",fp.read())
    fp.close()

    #add in checksys.sh
    generate_checksys(output_zip)
    #add in firstboot.sh
    generate_firstboot(output_zip)

    #add in bootcmdutil
    #out/target/product/sapphire/obj/EXECUTABLES/bootcmdutil_intermediates/bootcmdutil
    fp=open(os.path.join(android_root,
              "out","target","product","sapphire","obj","EXECUTABLES",
              "bootcmdutil_intermediates","bootcmdutil"),
              "rb")
    common.ZipWriteStr(output_zip,"kernel/bootcmdutil",fp.read())
    fp.close()
    
    #add eddify
    script.ShowProgress(0.2, 0)
    script.ShowProgress(0.2, 10)
    script.AppendExtra("""

#check the system information of the system we are installing on
package_extract_file("checksys.sh","/tmp/checksys.sh");
set_perm(0,0,755,"/tmp/checksys.sh");
run_program("/tmp/checksys.sh");

#determine if we need to patch a boot image
if file_getprop("/tmp/nfo.prop","radioseries") == "3.22"
then 
    #EBI1 kernel needed
    ui_print("Extracting EBI1 patch");
    package_extract_file("kernel/ebi1-boot.img","/tmp/boot.img");
    package_extract_file("kernel/ebi1-modules.sqf",
                         "/system/lib/modules/modules.sqf");
else
    #EBI0/2708 kernel needed
    if file_getprop("/tmp/nfo.prop","smisize") == "64" &&
       ( file_getprop("/tmp/nfo.prop","bootloader") == "1.33.0011" ||
         file_getprop("/tmp/nfo.prop","bootloader") == "1.33.2011" ||
         file_getprop("/tmp/nfo.prop","bootloader") == "1.33.3011" ||
         file_getprop("/tmp/nfo.prop","bootloader") == "1.33.0013" ||
         file_getprop("/tmp/nfo.prop","bootloader") == "1.33.2013" ||
         file_getprop("/tmp/nfo.prop","bootloader") == "1.33.3013" ||
         file_getprop("/tmp/nfo.prop","bootloader") == "1.33.0013d" ) &&
       ( file_getprop("/tmp/nfo.prop","baseband") == "2.22.27.08" ||
         file_getprop("/tmp/nfo.prop","baseband") == "2.22.28.25" )
    then
        #2708 kernel (unless the user has the fake Crios SPL 1.33.2013 ENG)
        # if the fake version they will fail to boot since its really
        # 1.33.2005...
        if file_getprop("/tmp/nfo.prop","bootloader") == "1.33.2013"
        then
            ui_print("1.33.2013 detected, please ensure this is not Crios SPL 1.33.2013 ENG; as its really 1.33.2005");
        endif;
        ui_print("Extracting 2708+ patch");
        package_extract_file("kernel/2708-boot.img","/tmp/boot.img");
    else
        #EBI0 kernel
        ui_print("Extracting EBI0 patch");
        package_extract_file("kernel/ebi0-boot.img","/tmp/boot.img");
        package_extract_file("kernel/ebi0-modules.sqf",
                             "/system/lib/modules/modules.sqf");
    endif;
endif;

#add the cMTD Command line if needed
if file_getprop("/tmp/nfo.prop","custommtd") == "CustomMTD"
then
    #extract recovery's command line option (thanks to Firerat)
    run_program("/sbin/sh","-c",
        "echo mtdparts`cat /proc/cmdline|awk -Fmtdparts '{print $2}'` >> /tmp/nfo.prop"
        );
    package_extract_file("kernel/bootcmdutil","/tmp/bootcmdutil");
    set_perm(0,0,755,"/tmp/bootcmdutil");
    ui_print("Applying cMTD to boot.img");
    run_program("/tmp/bootcmdutil","append","/tmp/boot.img",
                concat("mtdparts=",file_getprop("/tmp/nfo.prop","mtdparts"))
               );
    delete("/tmp/bootcmdutil");
endif;

ui_print("Write boot.img");
assert(write_raw_image("/tmp/boot.img","boot"));
delete("/tmp/checksys.sh","/tmp/boot.img");

#END INSTALL boot.img

#Install "Audio hack"

ui_print("AudioPara4.csv setup:");
if file_getprop("/tmp/nfo.prop","sysboard") == "trout"
then
    #we have a HTC Dream
    ui_print("system/etc/.audio/AudioPara_TMUS_DREA.csv.gz");
    run_program("/sbin/sh","-c",
           concat("busybox gzip -dc ",
                  "/system/etc/.audio/AudioPara_TMUS_DREA.csv.gz > ",
                  "/system/etc/AudioPara4.csv"));
else
    #We have one brand or other of HTC Sapphire
    if file_getprop("/tmp/nfo.prop","smisize") == "64"
    then
        #this is a 32B board
        ui_print("system/etc/.audio/AudioPara_TMUS_SAPP.csv.gz");
        run_program("/sbin/sh","-c",
               concat("busybox gzip -dc ",
                      "/system/etc/.audio/AudioPara_TMUS_SAPP.csv.gz > ",
                      "/system/etc/AudioPara4.csv"));
    else
        #this is a 32A baord
        ui_print("system/etc/.audio/AudioPara_VODA_SAPP.csv.gz");
        run_program("/sbin/sh","-c",
               concat("busybox gzip -dc ",
                      "/system/etc/.audio/AudioPara_VODA_SAPP.csv.gz > ",
                      "/system/etc/AudioPara4.csv"));
    endif;
endif;
#Ensure we sync.. I've seen files flashed at the end of a edify script like
#this vanish
run_program("/sbin/sh","-c","sleep 2; sync");

#now update permissions on the new file and we are done
set_perm(0, 0, 0644, "/system/etc/AudioPara4.csv");

#For smoother updates we also now want a firstboot script
mount("yaffs2", "MTD", "userdata", "/data");
package_extract_file("firstboot.sh","/data/firstboot.sh");
unmount("/data");
""")
    #clean up temporary files
    shutil.rmtree(temp_root,ignore_errors=True)


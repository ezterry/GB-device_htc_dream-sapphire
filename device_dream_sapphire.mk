#
# Copyright (C) 2008 The Android Open Source Project
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
#

DEVICE_PACKAGE_OVERLAYS := device/htc/dream-sapphire/overlay

# Install the features available on this device.
PRODUCT_COPY_FILES := \
    frameworks/base/data/etc/handheld_core_hardware.xml:system/etc/permissions/handheld_core_hardware.xml \
    frameworks/base/data/etc/android.hardware.camera.autofocus.xml:system/etc/permissions/android.hardware.camera.autofocus.xml \
    frameworks/base/data/etc/android.hardware.telephony.gsm.xml:system/etc/permissions/android.hardware.telephony.gsm.xml \
    frameworks/base/data/etc/android.hardware.location.gps.xml:system/etc/permissions/android.hardware.location.gps.xml \
    frameworks/base/data/etc/android.hardware.wifi.xml:system/etc/permissions/android.hardware.wifi.xml \
    frameworks/base/data/etc/android.hardware.touchscreen.multitouch.xml:system/etc/permissions/android.hardware.touchscreen.multitouch.xml \
    frameworks/base/data/etc/android.software.sip.voip.xml:system/etc/permissions/android.software.sip.voip.xml \
    frameworks/base/data/etc/android.software.sip.xml:system/etc/permissions/android.software.sip.xml \
    frameworks/base/data/etc/android.hardware.usb.accessory.xml:system/etc/permissions/android.hardware.usb.accessory.xml

#copy default modules.
PRODUCT_COPY_FILES += \
    device/htc/dream-sapphire/kernel/2708-modules.sqf:system/lib/modules/modules.sqf

#Copy init.d scripts
PRODUCT_COPY_FILES += \
    device/htc/dream-sapphire/prebuilt/etc/init.d/00banner:system/etc/init.d/00banner \
    device/htc/dream-sapphire/prebuilt/etc/init.d/04modules:system/etc/init.d/04modules \
    device/htc/dream-sapphire/prebuilt/etc/init.d/05mountsd:system/etc/init.d/05mountsd \
    device/htc/dream-sapphire/prebuilt/etc/init.d/06BindCache:system/etc/init.d/06BindCache \
    device/htc/dream-sapphire/prebuilt/etc/init.d/10apps2sd:system/etc/init.d/10apps2sd \
    device/htc/dream-sapphire/prebuilt/etc/init.d/12zram_compcache:system/etc/init.d/12zram_compcache

#Copy audio profiles
PRODUCT_COPY_FILES += \
    device/htc/dream-sapphire/prebuilt/etc/.audio/AudioPara_TMUS_DREA.csv.gz:system/etc/.audio/AudioPara_TMUS_DREA.csv.gz \
    device/htc/dream-sapphire/prebuilt/etc/.audio/AudioPara_TMUS_SAPP.csv.gz:system/etc/.audio/AudioPara_TMUS_SAPP.csv.gz \
    device/htc/dream-sapphire/prebuilt/etc/.audio/AudioPara_VODA_SAPP.csv.gz:system/etc/.audio/AudioPara_VODA_SAPP.csv.gz

#Copy prebuilt files
PRODUCT_COPY_FILES += \
    device/htc/dream-sapphire/prebuilt/bin/fix_permissions:system/bin/fix_permissions \
    device/htc/dream-sapphire/prebuilt/build.trout.prop:system/build.trout.prop

PRODUCT_PROPERTY_OVERRIDES += \
    ro.media.dec.jpeg.memcap=10000000

PRODUCT_PROPERTY_OVERRIDES += \
    rild.libpath=/system/lib/libhtc_ril.so \
    wifi.interface=tiwlan0

# Time between scans in seconds. Keep it high to minimize battery drain.
# This only affects the case in which there are remembered access points,
# but none are in range.
PRODUCT_PROPERTY_OVERRIDES += \
    wifi.supplicant_scan_interval=30

# density in DPI of the LCD of this board. This is used to scale the UI
# appropriately. If this property is not defined, the default value is 160 dpi. 
PRODUCT_PROPERTY_OVERRIDES += \
    ro.sf.lcd_density=160

# Default network type
# 0 => WCDMA Preferred.
PRODUCT_PROPERTY_OVERRIDES += \
    ro.telephony.default_network=0

# The OpenGL ES API level that is natively supported by this device.
# This is a 16.16 fixed point number
PRODUCT_PROPERTY_OVERRIDES += \
    ro.sf.hw=1 \
    ro.opengles.version=65537

# Set the vm heapsize to 18MB
PRODUCT_PROPERTY_OVERRIDES += \
    dalvik.vm.heapsize=18m

#Set purgeable assets to save ram on low mem devices
PRODUCT_PROPERTY_OVERRIDES += \
    persist.sys.purgeable_assets=1

#include ueventd.ds.rc when loading uevent rules
BOARD_INIT_USES_DS_UEVENT:=true

# Build ID for protected market apps
PRODUCT_PROPERTY_OVERRIDES += \
    ro.build.fingerprint=google/soju/crespo:2.3.1/GRH78/85442:user/release-keys

#rom identification
ifneq ($(ROMMANAGER_MOD_ID),)
ifneq ($(ROMMANAGER_DEVELOPER_ID),)
PRODUCT_PROPERTY_OVERRIDES += \
    ro.rommanager.developerid=$(ROMMANAGER_DEVELOPER_ID)
endif
PRODUCT_PROPERTY_OVERRIDES += \
    ro.modversion=ezGingerbread-$(ROMMANAGER_MOD_ID)
else
PRODUCT_PROPERTY_OVERRIDES += \
    ro.modversion=ezGingerbread-KANGED
endif


# media configuration xml file
PRODUCT_COPY_FILES += \
    device/htc/dream-sapphire/media_profiles.xml:/system/etc/media_profiles.xml

#System module location (for busybox modprobe)
KERNEL_MODULES_DIR=/system/lib/modules

#Use v8 Javascript engine
JS_ENGINE := v8

#use armv6j code
TARGET_ARCH_VARIANT := armv6j
TARGET_DVM_ARCH_VARIANT := armv5te

# proprietary side of the device
$(call inherit-product-if-exists, vendor/htc/dream-sapphire/device_dream_sapphire-vendor.mk)

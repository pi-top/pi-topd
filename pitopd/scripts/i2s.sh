#!/bin/bash -ex

# i2s.sh [enable|disable]
#   status/enable/disable
boot_partition_mountpont() {
	if [ -e /boot/firmware/config.txt ] ; then
		FIRMWARE="/firmware"
	else
		FIRMWARE=""
	fi
	echo "/boot${FIRMWARE}"
}

BOOT_MOUNTPOINT=$(boot_partition_mountpont)
CONFIG="${BOOT_MOUNTPOINT}/config.txt"
TEMP_ASOUND_CONF="/tmp/asound.conf.tmp"
BAK_ASOUND_CONF="/etc/asound.conf.bak"
ASOUND_CONF="/etc/asound.conf"

activeOverlayExists() {
  local overlay="$1"
  if [ -e $CONFIG ] && grep -q "^dtoverlay=$overlay$" $CONFIG; then
    true
  else
    false
  fi
}

inactiveOverlayExists() {
  local overlay="$1"
  if [ -e $CONFIG ] && grep -q "^#dtoverlay=$overlay$" $CONFIG; then
    true
  else
    false
  fi
}

activeParamExists() {
  local param="$1"
  if [ -e $CONFIG ] && grep -q "^dtparam=$param=on$" $CONFIG; then
    true
  else
    false
  fi
}

inactiveParamExists() {
  local param="$1"
  if [ -e $CONFIG ] && grep -q "^#dtparam=$param=on$" $CONFIG; then
    true
  else
    false
  fi
}

i2sIsEnabledThisSession() {
  if [[ "$(lsmod | grep rpi_simple_soundcard)" != "" ]]; then
    true
  else
    false
  fi
}

i2sIsToBeEnabledNextSession() {
  if activeOverlayExists i2s-mmap && activeOverlayExists hifiberry-dac && ! activeParamExists audio; then
    true
  else
    false
  fi
}

setDTOverlayState() {
  local overlay="$1"
  local enableOverlay=$2
  local line="dtoverlay=$overlay"
  if [ "$enableOverlay" -eq 0 ]; then
    echo -e "Attempting to enable $overlay overlay... \c"
    if activeOverlayExists "$overlay"; then
      echo "$overlay overlay already active - nothing to do"
    else
      echo "$overlay overlay not active - enabling"
      if inactiveOverlayExists "$overlay"; then
        sudo sed -i "s/^#$line$/$line/1" $CONFIG
      else
        echo "$line" | sudo tee -a $CONFIG &>/dev/null
      fi
    fi
  else
    echo -e "Attempting to disable $overlay overlay... \c"
    if activeOverlayExists "$overlay"; then
      echo "$overlay overlay active - disabling"
      sudo sed -i "s/^$line/#&/1" $CONFIG
    else
      echo "$overlay overlay not in device tree - nothing to do"
    fi
  fi
}

setDTParamState() {
  local param="$1"
  local enableParam=$2
  local line="dtparam=$param=on"

  if [ "$enableParam" -eq 0 ]; then
    if activeParamExists "$param"; then
      echo "$param param already active - nothing to do"
    else
      echo "$param param not active - enabling"
      if inactiveParamExists "$param"; then
        sudo sed -i "s/^#$line$/$line/1" $CONFIG
      else
        echo "$line" | sudo tee -a $CONFIG &>/dev/null
      fi
    fi
  else
    if activeParamExists "$param"; then
      echo "$param param active - disabling"
      sudo sed -i "s/^$line/#&/1" $CONFIG
    else
      echo "$param param not in device tree - nothing to do"
    fi
  fi
}

backupOrigAsoundConf() {
  if [ -e $ASOUND_CONF ]; then
    if [ -e $BAK_ASOUND_CONF ]; then
      echo "Deleting backup asound.conf"
      sudo rm -f $BAK_ASOUND_CONF
    fi
    echo "Creating backup non-I2S/original asound.conf"
    sudo mv $ASOUND_CONF $BAK_ASOUND_CONF
  fi
}

restoreOrigAsoundConf() {
  if [ -e $ASOUND_CONF ]; then
    echo "Deleting I2S asound.conf"
    sudo rm -f $ASOUND_CONF
  fi
  if [ -e $BAK_ASOUND_CONF ]; then
    echo "Restoring non-I2S/original asound.conf from backup"
    sudo mv $BAK_ASOUND_CONF $ASOUND_CONF
  fi
}

setCustomAsoundConfState() {
  local enableCustomConf=$1

  if [ "$enableCustomConf" -eq 0 ]; then

    backupOrigAsoundConf

    echo "Configuring custom asound.conf"

    echo -e "pcm.real {\n  type hw\n  card 0\n  device 0\n}" | sudo tee $TEMP_ASOUND_CONF &>/dev/null
    echo -e "pcm.dmixer {\n  type dmix\n  ipc_key 1024\n  ipc_perm 0666\n  slave.pcm \"real\"\n  slave {\n    period_time 0\n    period_size 1024\n    buffer_size 8192\n    rate 44100\n  }\n  bindings {\n    0 0\n    1 1\n  }\n}" | sudo tee -a $TEMP_ASOUND_CONF &>/dev/null
    echo -e "ctl.dmixer {\n  type hw\n  card 0\n}" | sudo tee -a $TEMP_ASOUND_CONF &>/dev/null
    echo -e "pcm.softvol {\n  type softvol\n  slave.pcm \"dmixer\"\n  control {\n    name \"PCM\"\n    card 0\n   }\n}" | sudo tee -a $TEMP_ASOUND_CONF &>/dev/null
    echo -e "pcm.\041default {\n   type plug\n   slave.pcm \"softvol\"\n}" | sudo tee -a $TEMP_ASOUND_CONF &>/dev/null
    sudo mv $TEMP_ASOUND_CONF $ASOUND_CONF
  else
    restoreOrigAsoundConf
  fi
}

if [ -z "$1" ] || [[ "$1" == "status" ]] || [[ "$1" == "enable" ]] || [[ "$1" == "disable" ]]; then
  if [ -z "$1" ] || [[ "$1" == "status" ]]; then
    desired_i2s_enabled_state=-1
  elif [[ "$1" == "enable" ]]; then
    desired_i2s_enabled_state=0
  elif [[ "$1" == "disable" ]]; then
    desired_i2s_enabled_state=1
  fi
else
  echo "Usage: i2s.sh [status|enable|disable]"
  exit 1
fi

if i2sIsEnabledThisSession; then
  echo "I2S is currently enabled" # This string is used by pt-peripherals-daemon
else
  echo "I2S is currently disabled" # This string is used by pt-peripherals-daemon
fi

if i2sIsToBeEnabledNextSession; then
  echo "I2S is due to be enabled on reboot"
  if [ $desired_i2s_enabled_state -eq 0 ]; then
    echo "Nothing to do - exiting"
    exit 0
  fi
else
  echo "I2S is due to be disabled on reboot"
  if [ $desired_i2s_enabled_state -eq 1 ]; then
    echo "Nothing to do - exiting"
    exit 0
  fi
fi

if [ -z "$1" ] || [[ "$1" == "status" ]]; then
  exit 0
fi

setDTOverlayState i2s-mmap $desired_i2s_enabled_state
setDTOverlayState hifiberry-dac $desired_i2s_enabled_state
setDTParamState audio $((1 - desired_i2s_enabled_state))
setDTParamState i2s $desired_i2s_enabled_state
setCustomAsoundConfState $desired_i2s_enabled_state

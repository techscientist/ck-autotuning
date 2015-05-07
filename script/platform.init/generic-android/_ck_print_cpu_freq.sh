echo "*** Current frequency from scaling:"
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq

#echo "*** Current frequency from cpuinfo:"
#cat /sys/devices/system/cpu/cpu*/cpufreq/cpuinfo_cur_freq

echo "*** Min frequency:"
cat /sys/devices/system/cpu/cpu*/cpufreq/cpuinfo_min_freq

echo "*** Max frequency:"
cat /sys/devices/system/cpu/cpu*/cpufreq/cpuinfo_max_freq

echo "*** Available governors:"
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_available_governors

echo "*** Available frequencies:"
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_available_frequencies
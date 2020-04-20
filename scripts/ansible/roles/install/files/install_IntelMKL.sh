#!/bin/bash
##
## cf https://software.intel.com/en-us/articles/installing-intel-free-libs-and-python-apt-repo

cd /tmp
wget --no-verbose https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS-2019.PUB
apt-key add GPG-PUB-KEY-INTEL-SW-PRODUCTS-2019.PUB


## all products:
#sudo wget https://apt.repos.intel.com/setup/intelproducts.list -O /etc/apt/sources.list.d/intelproducts.list
## just MKL
sh -c 'echo deb https://apt.repos.intel.com/mkl all main > /etc/apt/sources.list.d/intel-mkl.list'
## other (TBB, DAAL, MPI, ...) listed on page

apt-get update
apt-get --yes install intel-mkl-64bit-2018.2-046   ## wants 500+mb :-/  installs to 1.8 gb :-/



## update alternatives
update-alternatives --install /usr/lib/x86_64-linux-gnu/libblas.so     libblas.so-x86_64-linux-gnu      /opt/intel/mkl/lib/intel64/libmkl_rt.so 150
update-alternatives --install /usr/lib/x86_64-linux-gnu/libblas.so.3   libblas.so.3-x86_64-linux-gnu    /opt/intel/mkl/lib/intel64/libmkl_rt.so 150
update-alternatives --install /usr/lib/x86_64-linux-gnu/liblapack.so   liblapack.so-x86_64-linux-gnu    /opt/intel/mkl/lib/intel64/libmkl_rt.so 150
update-alternatives --install /usr/lib/x86_64-linux-gnu/liblapack.so.3 liblapack.so.3-x86_64-linux-gnu  /opt/intel/mkl/lib/intel64/libmkl_rt.so 150

## connect for IntelPython repository pip installs (mlk_fft, mlk_random, mlk_service)
## They require it in /usr/lib/x86_64-linux-gnu/, /usr/lib/ or /usr/local/lib/
ln -s /opt/intel/mkl/lib/intel64/libmkl_rt.so /usr/lib/x86_64-linux-gnu/libmkl_rt.so
# IntelPython needs all header files 
for filename in "$(cd /opt/intel/mkl && cd ./include && pwd)"/*; do 
	[ -f "$filename" ] && ln -s "$filename" /usr/local/include/;  
done;

## mkl config knows install location
echo "/opt/intel/lib/intel64"     >  /etc/ld.so.conf.d/mkl.conf
echo "/opt/intel/mkl/lib/intel64" >> /etc/ld.so.conf.d/mkl.conf
ldconfig

echo "MKL_THREADING_LAYER=GNU" >> /etc/environment

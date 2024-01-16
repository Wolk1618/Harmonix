# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/thomas/esp/esp-idf/components/bootloader/subproject"
  "/home/thomas/Documents/Imperial/lab/repo/ranging_basic/build/bootloader"
  "/home/thomas/Documents/Imperial/lab/repo/ranging_basic/build/bootloader-prefix"
  "/home/thomas/Documents/Imperial/lab/repo/ranging_basic/build/bootloader-prefix/tmp"
  "/home/thomas/Documents/Imperial/lab/repo/ranging_basic/build/bootloader-prefix/src/bootloader-stamp"
  "/home/thomas/Documents/Imperial/lab/repo/ranging_basic/build/bootloader-prefix/src"
  "/home/thomas/Documents/Imperial/lab/repo/ranging_basic/build/bootloader-prefix/src/bootloader-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/thomas/Documents/Imperial/lab/repo/ranging_basic/build/bootloader-prefix/src/bootloader-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/thomas/Documents/Imperial/lab/repo/ranging_basic/build/bootloader-prefix/src/bootloader-stamp${cfgdir}") # cfgdir has leading slash
endif()

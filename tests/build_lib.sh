pushd cuv-test-project
rm -rf build
mkdir -p build
pushd build
cmake -G Ninja .. -DCMAKE_TOOLCHAIN_FILE=../toolchain/toolchain.cmake
ninja


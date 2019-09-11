#include "hash.hh"
#include <cstring>

extern "C" const char* nix_build_hash_base32_to_base16_c_str(const char* hash_base32_c_str) {
  printf("%s\n", hash_base32_c_str);
  // somewhy doing this in a single expr produces garbage
  std::string hash_base16_cxx_str = nix::Hash(hash_base32_c_str, nix::htSHA1).to_string(nix::Base16);
  const char* hash_base16_c_str = hash_base16_cxx_str.c_str();
  // we can't return hash_base16_c_str, it's stack pointer which has no sense in callee function
  // solution: copy to heap
  char* hash_base16_c_str_heap = new char[strlen(hash_base16_c_str)];
  strcpy(hash_base16_c_str_heap, hash_base16_c_str);
  return hash_base16_c_str_heap;
  //return nix_build_hash_base32_to_base16_cppstr(hash_str).c_str();
}

extern "C" int main() {
  printf("%s", nix_build_hash_base32_to_base16_c_str("pgbd92jc5bv6vnh7gfmgbhfbbxq0sdpp"));
  return 0;
}

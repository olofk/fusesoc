#include <stdio.h>

FILE* load_elf_file(char* elf_file_name);
long get_size(FILE* bin_file);
unsigned int read_32(FILE* bin_file, unsigned int address);

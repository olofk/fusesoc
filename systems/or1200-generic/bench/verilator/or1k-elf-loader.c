#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>


FILE* load_elf_file(char *elf_file_name) {
  const char *objcopy_arg = "or1k-elf-objcopy -O binary";
  FILE *bin_file;
  char *bin_file_name = NULL;
  char *system_args = NULL;

  //FIXME: Pipe objcopy output directly to bin file
  if(access (elf_file_name, R_OK)) 
    return NULL;

  bin_file_name = malloc(L_tmpnam);

  if(!tmpnam(bin_file_name))
    return NULL;

  system_args = malloc(strlen(objcopy_arg) + strlen(elf_file_name) + 1 + strlen(bin_file_name));
  sprintf(system_args, "%s %s %s", objcopy_arg, elf_file_name, bin_file_name);
  if(system(system_args))
    return NULL;

  bin_file = fopen(bin_file_name, "r");
  remove(bin_file_name);

  if(bin_file_name)
    free(bin_file_name);
  if(system_args)
    free(system_args);
  return bin_file;
}

long get_size(FILE *bin_file) {
  long file_size;
  fseek(bin_file, 0L, SEEK_END);
  file_size = ftell(bin_file);
  return file_size;
}

unsigned int read_32(FILE *bin_file, unsigned int address) {
  unsigned int data;
  unsigned int swapped;

  fseek(bin_file, address, SEEK_SET);
  if(fread(&data, sizeof(int), 1, bin_file));
  swapped = ((data>>24)&0xff) | // move byte 3 to byte 0
    ((data<<8)&0xff0000) | // move byte 1 to byte 2
    ((data>>8)&0xff00) | // move byte 2 to byte 1
    ((data<<24)&0xff000000); // byte 0 to byte 3  

  return swapped;
}

unsigned short read_16(FILE *bin_file, unsigned int address) {
  unsigned short data;
  unsigned short swapped;

  fseek(bin_file, address, SEEK_SET);
  if(fread(&data, sizeof(short), 1, bin_file));
  swapped = ((data>>8)&0x00ff) | // move byte 1 to byte 0
            ((data<<8)&0xff00);  // move byte 0 to byte 1  

  return swapped;
}

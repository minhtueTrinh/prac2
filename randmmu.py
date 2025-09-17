import random
from mmu import MMU

class RandMMU(MMU):
    def __init__(self, frames):
        self.num_frames = frames
        self.frames = {} 
        self.ptable = {} 
        self.disk_reads = 0
        self.disk_writes = 0
        self.page_faults = 0
        self.debug = False

    def set_debug(self):
        self.debug = True

    def reset_debug(self):
        self.debug = False

    def read_memory(self, page_number):
        if page_number in self.ptable:
            if self.debug == True:
                print(f"hit: page ({page_number}). frame = {self.ptable[page_number]}")
            return  # hit
        else:
            # Page fault
            self.page_faults += 1
            self.disk_reads += 1
            if len(self.frames) < self.num_frames:
                # Free frame available
                frame_index = len(self.frames)
                self.frames[frame_index] = page_number
                self.ptable[page_number] = frame_index
                if self.debug:
                    print(f"fault: load {page_number} into frame {frame_index}")
            else:
                #find a frame to become sacrificial object
                sheep = random.choice(list(self.frames.keys()))
                sheepage = self.frames[sheep]


                self.frames[sheep] = page_number
                self.ptable.pop(sheepage)
                self.ptable[page_number] = sheep

                if self.debug == True:
                    print(f"read fault: replaced {sheepage} with {page_number} in frame {sheep}")

    def write_memory(self, page_number):
        if page_number in self.ptable:
            if self.debug == True:
                print(f"WRITE HIT: page {page_number} in frame {self.ptable[page_number]}")
        else:
            self.page_faults += 1
            self.disk_reads += 1
            if len(self.frames) < self.num_frames:
                frame_index = len(self.frames)
                self.frames[frame_index] = page_number
                self.ptable[page_number] = frame_index
                if self.debug:
                    print(f"WRITE FAULT: loaded page {page_number} into free frame {frame_index}")
            else:
                sheep = random.choice(list(self.frames.keys()))
                sheepage = self.frames[sheep]

                self.disk_writes += 1

                self.frames[sheep] = page_number
                self.ptable.pop(sheepage)
                self.ptable[page_number] = sheep

                if self.debug == True:
                    print(f"WRITE FAULT: replaced page {sheepage} with {page_number} in frame {sheep}")

    def get_total_disk_reads(self):
        return self.disk_reads

    def get_total_disk_writes(self):
        return self.disk_writes

    def get_total_page_faults(self):
        return self.page_faults
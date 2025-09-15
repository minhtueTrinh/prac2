from mmu import MMU

class LruMMU(MMU):
    def __init__(self, frames):
        # TODO: Constructor logic for LruMMU
        self.num_frames = frames
        self.debug_mode = False
        
        # Stat counters
        self.disk_reads = 0
        self.disk_writes = 0
        self.page_faults = 0
        self.page_table = {}
        self.frame_table = [None] * frames
        self.dirty_pages = {}
        self.lru_list = []
        self.occupied_frames = set()

    def set_debug(self):
        # TODO: Implement the method to set debug mode
        self.debug_mode = True

    def reset_debug(self):
         # TODO: Implement the method to reset debug mode
        self.debug_mode = False

    def read_memory(self, page_number):
        # TODO: Implement the method to read memory
        if self.debug_mode:
            print(f"READ: Page {page_number}")
        
        if page_number in self.page_table:
            # Page hit - update LRU order
            if page_number in self.lru_list:
                self.lru_list.remove(page_number)
            self.lru_list.insert(0, page_number)
            
            if self.debug_mode:
                print(f"  HIT: Page {page_number} in frame {self.page_table[page_number]}")
        else:
            # Page fault
            self.page_faults += 1
            if self.debug_mode:
                print(f"  PAGE FAULT: Page {page_number}")
            
            # Find frame to use
            frame_num = None
            for i in range(self.num_frames):
                if i not in self.occupied_frames:
                    frame_num = i
                    break
            
            if frame_num is None:
                # Evict LRU page
                victim_page = self.lru_list[-1]  # Last is LRU
                frame_num = self.page_table[victim_page]
                
                # Write to disk if dirty
                if victim_page in self.dirty_pages and self.dirty_pages[victim_page]:
                    self.disk_writes += 1
                    if self.debug_mode:
                        print(f"  DISK WRITE: Page {victim_page}")
                
                # Remove victim page
                del self.page_table[victim_page]
                self.frame_table[frame_num] = None
                self.occupied_frames.remove(frame_num)
                self.lru_list.remove(victim_page)
                
                if self.debug_mode:
                    print(f"  EVICT: Page {victim_page} from frame {frame_num}")
            
            # Load new page
            self.disk_reads += 1
            if self.debug_mode:
                print(f"  DISK READ: Page {page_number}")
            
            self.page_table[page_number] = frame_num
            self.frame_table[frame_num] = page_number
            self.occupied_frames.add(frame_num)
            self.dirty_pages[page_number] = False
            
            # Update LRU
            self.lru_list.insert(0, page_number)
            
            if self.debug_mode:
                print(f"  LOAD: Page {page_number} into frame {frame_num}")

    def write_memory(self, page_number):
        # TODO: Implement the method to write memory
        if self.debug_mode:
            print(f"WRITE: Page {page_number}")
        
        if page_number in self.page_table:
            # Page hit - mark and update LRU
            self.dirty_pages[page_number] = True
            if page_number in self.lru_list:
                self.lru_list.remove(page_number)
            self.lru_list.insert(0, page_number)
            
            if self.debug_mode:
                print(f"  HIT: Page {page_number} in frame {self.page_table[page_number]} (marked dirty)")
        else:
            # Page fault
            self.page_faults += 1
            if self.debug_mode:
                print(f"  PAGE FAULT: Page {page_number}")
            
            # Find frame to use
            frame_num = None
            for i in range(self.num_frames):
                if i not in self.occupied_frames:
                    frame_num = i
                    break
            
            if frame_num is None:
                # Evict LRU page
                victim_page = self.lru_list[-1]  # Last is LRU
                frame_num = self.page_table[victim_page]
                
                # Write to disk if dirty
                if victim_page in self.dirty_pages and self.dirty_pages[victim_page]:
                    self.disk_writes += 1
                    if self.debug_mode:
                        print(f"  DISK WRITE: Page {victim_page}")
                
                # Remove victim page
                del self.page_table[victim_page]
                self.frame_table[frame_num] = None
                self.occupied_frames.remove(frame_num)
                self.lru_list.remove(victim_page)
                
                if self.debug_mode:
                    print(f"  EVICT: Page {victim_page} from frame {frame_num}")
            
            # Load new page
            self.disk_reads += 1
            if self.debug_mode:
                print(f"  DISK READ: Page {page_number}")
            
            self.page_table[page_number] = frame_num
            self.frame_table[frame_num] = page_number
            self.occupied_frames.add(frame_num)
            self.dirty_pages[page_number] = True
            
            # Update LRU
            self.lru_list.insert(0, page_number)
            
            if self.debug_mode:
                print(f"  LOAD: Page {page_number} into frame {frame_num}")

    def get_total_disk_reads(self):
        # TODO: Implement the method to get total disk reads
        return self.disk_reads

    def get_total_disk_writes(self):
        # TODO: Implement the method to get total disk writes
        return self.disk_writes

    def get_total_page_faults(self):
        # TODO: Implement the method to get total page faults
        return self.page_faults

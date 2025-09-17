from mmu import MMU


class ClockMMU(MMU):
    def __init__(self, frames):
        # TODO: Constructor logic for ClockMMU
        if frames < 1:
            raise ValueError("Frame number must be at least 1")
        self.frames_capacity = frames
        self.frames = [None] * self.frames_capacity #list of dicts: {page_number, reference_bit, dirty_bit}
        self.hand = 0 #pointer for clock algorithm. Poiting to the next frame to check
        
        #Hand = index that scans frames 
        #Victim = frame under the hand when its reference bit is 0
        
        self.page_to_index = {} #fast lookup for page_number
        
        #number of used frames (<= capacity)
        self.used = 0
        
        #counters
        self.page_faults = 0
        self.disk_reads = 0
        self.disk_writes = 0
        
        #debug mode
        self.debug = False

    def set_debug(self):
        # TODO: Implement the method to set debug mode
        self.debug = True

    def reset_debug(self):
        # TODO: Implement the method to reset debug mode
        self.debug = False

    def read_memory(self, page_number):
        # TODO: Implement the method to read memory
        #HIT 
        for i, frame in enumerate(self.frames):
            if frame is not None and frame['page_number'] == page_number:
                frame['reference_bit'] = 1
                if self.debug:
                    print(f"Read hit: page {page_number} found in frame {i}")
                return
        #MISS
        self.page_faults += 1
        self.disk_reads += 1
        if self.debug:
            print(f"Read miss: page {page_number} not found, page fault #{self.page_faults}")
            
        #check for free frame
        if self.used < self.frames_capacity:
            for idx in range(self.frames_capacity):
                if self.frames[idx] is None:
                    self.frames[idx] = {'page_number': page_number, 'reference_bit': 1, 'dirty_bit': 0}
                    self.page_to_index[page_number] = idx
                    self.used += 1
                    if self.debug:
                        print(f"Loaded page {page_number} into free frame {idx}")
                    return
        #eviction 
        while True:
            current_frame = self.frames[self.hand]
            if current_frame['reference_bit'] == 1:
                current_frame['reference_bit'] = 0
                if self.debug:
                    print(f"Frame {self.hand} reference bit set to 0, moving hand")
                self.hand = (self.hand + 1) % self.frames_capacity
                continue
                
            #if ref bit == 0 --> evict
            victim_frame = self.hand
            victim = self.frames[victim_frame]
            if victim['dirty_bit'] == 1:
                self.disk_writes += 1
                if self.debug:
                    print(f"Evicting dirty page {victim['page_number']} from frame {victim_frame}, writing to disk")
            else:
                if self.debug:
                    print(f"Evicting clean page {victim['page_number']} from frame {victim_frame}")
                    
            #replace with new page
            self.frames[victim_frame] = {'page_number': page_number, 'reference_bit': 1, 'dirty_bit': 0}
            
            #move to the next frame after eviction
            self.hand = (self.hand + 1) % self.frames_capacity
            if self.debug:
                print(f"Loaded page {page_number} into frame {victim_frame}")
            break

    def write_memory(self, page_number):
        #HIT similar to read_memory but set dirty bit
        for i, frame in enumerate(self.frames):
            if frame is not None and frame['page_number'] == page_number:
                frame['reference_bit'] = 1
                frame['dirty_bit'] = 1
                if self.debug:
                    print(f"Write hit: page {page_number} found in frame {i}, marked dirty")
                return
        #MISS
        self.page_faults += 1
        self.disk_reads += 1
        if self.debug:
            print(f"Write miss: page {page_number} not found, page fault #{self.page_faults}")
            
        #check for free frame
        if self.used < self.frames_capacity:
            for idx in range(self.frames_capacity):
                if self.frames[idx] is None:
                    self.frames[idx] = {'page_number': page_number, 'reference_bit': 1, 'dirty_bit': 1}
                    self.page_to_index[page_number] = idx
                    self.used += 1
                    if self.debug:
                        print(f"Loaded page {page_number} into free frame {idx}, marked dirty")
                    return
        #eviction using clock algorithm
        while True:
            current_frame = self.frames[self.hand]
            if current_frame['reference_bit'] == 1:
                current_frame['reference_bit'] = 0
                if self.debug:
                    print(f"Frame {self.hand} reference bit set to 0, moving hand")
                self.hand = (self.hand + 1) % self.frames_capacity
                continue
                
            #if ref bit == 0 --> evict
            victim_frame = self.hand
            victim = self.frames[victim_frame]
            if victim['dirty_bit'] == 1:
                self.disk_writes += 1
                if self.debug:
                    print(f"Evicting dirty page {victim['page_number']} from frame {victim_frame}, writing to disk")
            else:
                if self.debug:
                    print(f"Evicting clean page {victim['page_number']} from frame {victim_frame}")
                    
            #replace with new page, mark dirty
            self.frames[victim_frame] = {'page_number': page_number, 'reference_bit': 1, 'dirty_bit': 1}
            
            #move to the next frame after eviction
            self.hand = (self.hand + 1) % self.frames_capacity
            if self.debug:
                print(f"Loaded page {page_number} into frame {victim_frame}, marked dirty")
            break

    def get_total_disk_reads(self):
        # TODO: Implement the method to get total disk reads
        return self.disk_reads

    def get_total_disk_writes(self):
        # TODO: Implement the method to get total disk writes
        return self.disk_writes

    def get_total_page_faults(self):
        # TODO: Implement the method to get total page faults
        return self.page_faults

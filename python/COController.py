import math, os, time, logging, copy
# TODO: Fix the import path
import SLABHIDtoSMBUS as i2c

log = logging.getLogger(__name__)

class Controller(object):
    fcvo_min_ = 10800000000.0
    hsdiv_upper_limit_ = 2046
    hsdiv_lower_limit_odd_ = 5
    hsdiv_upper_limit_odd_ = 33
    xtal_freq_ = 55050000.0
    data_addr_ = ['FF', '45', '11', '17', '1A', '07', '11']
    data_data_ = ['00', '00', '00', '1C02', 'FBE86E2FC400', '08', '01']
    slave_addr_ = int('55', 16) << 1  # the left shift is for CP2112's convention

    def __init__(self):
        if i2c.GetNumDevices() > 1:
            raise RuntimeError("There are more than 1 CP2112 connected.")
        if i2c.IsOpened():
            raise RuntimeError("Failed to initialize, CP2112 has been opened by other program.")
        log.info("Start connecting to CP2112 ...")
        self.smb_ = i2c.HidSmbusDevice()
        self.smb_.Open()
        self.smb_.SetSmbusConfig(transferRetries=1)
        log.info("CP2112 has been successfully opened.")

    def __del__(self):
        self.smb_.close()

    def _freq_to_code(self, frequency, setup_hex):
        if frequency > 250e6 or frequency < 0:
            setup_hex[:] = []
            return False
        min_hsls_div = self.fcvo_min_ / frequency
        lsdiv_div = math.ceil(min_hsls_div / self.hsdiv_upper_limit_)
        if (lsdiv_div > 32):
            lsdiv_div = 32
        lsdiv_reg = math.ceil(math.log(lsdiv_div, 2))
        lsdiv_div = 2 ** lsdiv_reg
        hsdiv = math.ceil(min_hsls_div / lsdiv_div)
        if ((lsdiv_reg > 0) or ((hsdiv >= self.hsdiv_lower_limit_odd_) and (hsdiv <= self.hsdiv_upper_limit_odd_))):
            hsdiv = hsdiv # leaves hsdiv as even or odd only if lsdiv_div = 1 and hsdiv is from 5 to 33.
        elif ((hsdiv % 2) != 0) : #if hsdiv is an odd value...
            hsdiv = hsdiv + 1 #...make it even by rounding up
    
        fvco = (hsdiv * lsdiv_div * frequency)
        fbdiv = fvco / self.xtal_freq_
        #calculate 11.32 fixed point fbdiv value (mctl_m)
        (fbdiv_frac_t, fbdiv_int) = math.modf(fbdiv)
        (_, fbdiv_frac) = math.modf(fbdiv_frac_t * (2**32))
        fbdiv_frac = int(fbdiv_frac)
        fbdiv_int = int(fbdiv_int)
    
        #generate register values based on lsdiv, hsdiv, and fbdiv (mctl_m)
        reg23 = hsdiv & 0xff
        reg24 = ((hsdiv >> 8) & 0x7) | ((lsdiv_reg & 0x7) << 4)
        reg26 = (fbdiv_frac & 0xff)
        reg27 = (fbdiv_frac >> 8) & 0xff
        reg28 = (fbdiv_frac >> 16) & 0xff
        reg29 = (fbdiv_frac >> 24) & 0xff
        reg30 = (fbdiv_int) & 0xff
        reg31 = (fbdiv_int >> 8) & 0x7
        
        setup_hex[:] = ["%0.2x" % reg23, "%0.2x" % reg24, "%0.2x" % reg26, "%0.2x" % reg27, "%0.2x" % reg28, "%0.2x" % reg29, "%0.2x" % reg30, "%0.2x" % reg31]
        return True

    def send_frequency(self, frequency):
        freq_setup_hex = []
        if not self._freq_to_code(frequency, freq_setup_hex):
            raise ValueError("Input freq must be with in range [0-250e6]")
        data = copy.copy(self.data_data_)
        data[3] = freq_setup_hex[0:2]
        data[4] = freq_setup_hex[2:8]
        for ii in range(7):
            write_data = list(self.data_addr_[ii:ii+1])
            if ii == 3 or ii == 4:
                write_data.extend(data[ii])
            else:
                write_data.append(data[ii])
            self.smb_.WriteRequest(self.slave_addr_, list(map(int, write_data, [16]*len(write_data))))
            self.smb_.TransferStatusRequest()
            ret = self.smb_.GetTransferStatusResponse()
            time.sleep(0.2)
            if ret[0] != 2 or ret[1] != 5:
                log.error("Failed to send code: {0} to CP2112 device, return status: {0}".format(write_data), ret)
                return True
            return False
        




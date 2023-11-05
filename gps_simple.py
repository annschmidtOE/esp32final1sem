# A simple GPS library parsing the $GPGGA, $GPRMC and $GPZDA
# Developed on u-blox NEO-7M, milliseconds are not parsed


class GPS_SIMPLE:
    __nmeaBuffer = ""                       # NMEA receive buffer
    
    __utcYear = 0                           # UTC
    __utcMonth = 0
    __utcDay = 0
    __utcHours = 0
    __utcMinutes = 0
    __utcSeconds = 0

    __latitude = -999.0                     # Decimal degrees
    __longitude = -999.0                    # Decimal degrees
    __altitude = 0.0                        # in m

    __validity = "V"                        # Void
    __fixQuality = 0                        # 0: invalid, 1: GPS, 2: DGPS
    __satellites = 0
    __hdop = 0.0
    
    __speed = 0
    __course = 0.0
    
    __framesReceived = 0                    # May be queried to find out if even invaldi frames have been received
                                            # GGA = 0x0001, RMC = 0x0002 and ZDA = 0x0040, see other bits below
    
    def __init__(self, uart, all_nmea = False):
        self.uart = uart
        self.all_nmea = all_nmea

        # Enable relevant and wanted NMEA frames
        uart.write("$PUBX,40,GGA,1,1,1,0*5B\n")     # Make sure the $GPGGA, $GPRMC and $GPZDA are always enabled
        uart.write("$PUBX,40,RMC,1,1,1,0*46\n")
        uart.write("$PUBX,40,ZDA,1,1,1,0*45\n")

        if self.all_nmea == True:
            uart.write("$PUBX,40,GLL,1,1,1,0*5D\n") # Enable the rest of the NMEA frames, 0x0008
            uart.write("$PUBX,40,GRS,1,1,1,0*5C\n") # 0x0010
            uart.write("$PUBX,40,GSA,1,1,1,0*4F\n") # 0x0020
            uart.write("$PUBX,40,GST,1,1,1,0*5A\n") # 0x0040
            uart.write("$PUBX,40,GSV,1,1,1,0*58\n") # 0x0080
            uart.write("$PUBX,40,VTG,1,1,1,0*5F\n") # 0x0100
        else:  
            uart.write("$PUBX,40,GLL,0,0,0,0*5C\n") # Disable all but the $GPGGA,$GPRMC and $GPZDA frames
            uart.write("$PUBX,40,GRS,0,0,0,0*5D\n")
            uart.write("$PUBX,40,GSA,0,0,0,0*4E\n")
            uart.write("$PUBX,40,GST,0,0,0,0*5B\n")
            uart.write("$PUBX,40,GSV,0,0,0,0*59\n")
            uart.write("$PUBX,40,VTG,0,0,0,0*5E\n")            


    def __parse_nmea_frame(self, string):   # Change to parse all relevant frames: http://aprs.gids.nl/nmea/, no checksum validation
        
        subFrame = string.split(',')        # Split the NMEA frame into parts
        
        if len(subFrame[0]) < 6:            # No real data received
            return


        # Parse $GPGGA
        if subFrame[0] == "$GPGGA":         # $GPGGA,205019.00,5449.69634,N,01156.28487,E,1,12,0.98,29.3,M,39.7,M,,*6B
            self.__framesReceived |= 0x0001 # Set the frame ID bit

            # UTC hours, minutes and seconds
            if len(subFrame[1]) > 5:
                self.__utcHours = int(subFrame[1][0:2])
                self.__utcMinutes = int(subFrame[1][2:4])
                self.__utcSeconds = int(subFrame[1][4:6])
        
            # Latitude
            if len(subFrame[2]) > 0:
                laf = float(subFrame[2])
                lai = int(laf / 100)
                lad = (laf - lai * 100) / 60.0  # Convert to decimal degrees
                self.__latitude = lai + lad
                if subFrame[3] == "S":
                    self.__latitude = -latitude
            
            # Longitude
            if len(subFrame[4]) > 0:
                lof = float(subFrame[4])
                loi = int(lof / 100)
                lod = (lof - loi * 100) / 60.0  # Convert to decimal degrees
                self.__longitude = loi + lod
                if subFrame[5] == "W":
                    self.__longitude = -longitude
        
            # Fix quality, higher is better
            if len(subFrame[6]) > 0:
                self.__fixQuality = int(subFrame[6])
        
            # Number of satellites, higher is better
            if len(subFrame[7]) > 0:
                self.__satellites = int(subFrame[7])
        
            # HDOP, less is better
            if len(subFrame[8]) > 0:
                self.__hdop = float(subFrame[8])
        
            # Altitude
            if len(subFrame[9]) > 0:
                self.__altitude = float(subFrame[9])
   

        # Parse $GPRMC                        
        elif subFrame[0] == "$GPRMC":       # $GPRMC,081836.00,A,3751.65,S,14507.36,E,000.0,360.0,130998,011.3,E*62
            self.__framesReceived |= 0x0002 # Set the frame ID bit

            # UTC hours, minutes and seconds
            if len(subFrame[1]) > 5:
                self.__utcHours = int(subFrame[1][0:2])
                self.__utcMinutes = int(subFrame[1][2:4])
                self.__utcSeconds = int(subFrame[1][4:6])
        
            # Validity
            if len(subFrame[2]) > 0:
                self.__validity = subFrame[2]
                
            # Latitude
            if len(subFrame[3]) > 0:
                laf = float(subFrame[3])
                lai = int(laf / 100)
                lad = (laf - lai * 100) / 60.0  # Convert to decimal degrees
                self.__latitude = lai + lad
                if subFrame[4] == "S":
                    self.__latitude = -latitude                

            # Longitude
            if len(subFrame[5]) > 0:
                lof = float(subFrame[5])
                loi = int(lof / 100)
                lod = (lof - loi * 100) / 60.0  # Convert to decimal degrees
                self.__longitude = loi + lod
                if subFrame[6] == "W":
                    self.__longitude = -longitude
        
            # Speed, m/s
            if len(subFrame[7]) > 0:
                self.__speed = float(subFrame[7]) * 1852 / 3600
        
            # Course, °
            if len(subFrame[8]) > 0:
                self.__course = float(subFrame[6])
        
            # UTC year, month, day
            if len(subFrame[9]) > 5:
                self.__utcDay = int(subFrame[9][0:2])
                self.__utcMonth = int(subFrame[9][2:4])
                self.__utcYear = 2000 + int(subFrame[9][4:6])


        # Parse $GPZDA
        elif subFrame[0] == "$GPZDA":           # $GPZDA,143042.00,25,08,2005,,*6E
            self.__framesReceived |= 0x0004     # Set the frame ID bit
            
            # UTC hours, minutes and seconds       
            if len(subFrame[1]) > 5:
                self.__utcHours = int(subFrame[1][0:2])
                self.__utcMinutes = int(subFrame[1][2:4])
                self.__utcSeconds = int(subFrame[1][4:6])
            
            # UTC day
            if len(subFrame[2]) > 0:
                self.__utcDay = int(subFrame[2])
                
            # UTC month
            if len(subFrame[3]) > 0:
                self.__utcMonth = int(subFrame[3])

            # UTC year
            if len(subFrame[4]) > 0:
                self.__utcYear = int(subFrame[4])
        
        
        # Check if other frames are received and if so set the frame ID bit
        elif subFrame[0] == "$GPGLL":
            self.__framesReceived |= 0x0008      # Set the frame ID bit
        elif subFrame[0] == "$GPGRS":
            self.__framesReceived |= 0x0010      # Set the frame ID bit
        elif subFrame[0] == "$GPGSA":
            self.__framesReceived |= 0x0020      # Set the frame ID bit
        elif subFrame[0] == "$GPGST":
            self.__framesReceived |= 0x0040      # Set the frame ID bit
        elif subFrame[0] == "$GPGSV":
            self.__framesReceived |= 0x0080      # Set the frame ID bit
        elif subFrame[0] == "$GPVTG":
            self.__framesReceived |= 0x0100      # Set the frame ID bit


    def get_utc_year(self):
        return self.__utcYear


    def get_utc_month(self):
        return self.__utcMonth


    def get_utc_day(self):
        return self.__utcDay
    
    def get_utc_hours(self):
        return self.__utcHours


    def get_utc_minutes(self):
        return self.__utcMinutes


    def get_utc_seconds(self):
        return self.__utcSeconds


    def get_latitude(self):
        return self.__latitude


    def get_longitude(self):
        return self.__longitude


    def get_fix_quality(self):
        return self.__fixQuality


    def get_satellites(self):
        return self.__satellites


    def get_hdop(self):
        return self.__hdop


    def get_altitude(self):
        return self.__altitude
    
    
    def get_validity(self):
        return self.__validity

    
    def get_speed(self):
        return self.__speed
    
    
    def get_course(self):
        return self.__course

    
    def get_frames_received(self):
        return self.__framesReceived
    
    
    def clear_frames_received(self):
        self.__framesReceived = 0


    def write(self, string):
        self.uart.write(string, end = '')
        return 
    

    # The receiver funtion, call at least once per second
    def receive_nmea_data(self, echo = False):           # Returns true if data was parsed, otherwise false
        self.__nmeaBuffer
      
        if self.uart.any() > 0:
            string = self.uart.readline()                # Collect incoming chars
            try:
                self.__nmeaBuffer += string.decode("utf-8")  # UART returns bytes. They have to be conv. to chars/a string
            
                if "\n" in self.__nmeaBuffer:
                    self.__parse_nmea_frame(self.__nmeaBuffer)
                    if echo:
                        print(self.__nmeaBuffer, end = '')   # Echo the received frame
                    self.__nmeaBuffer = ""
              
                    return True
            except:
                return False
            
        return False
    
       
# EOF ##################################################################



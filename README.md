# Embed ZOOM recordings into moodle courses from S3 bucket 





- m3u8 streaming
- Add watermark
- Easy import from moodle repository
- Cloudfront private key to restrict access


# Example Database table structure
  
CREATE TABLE `zoom_recordings` (  
  `insertId` int(11) NOT NULL,  
  `start_time` varchar(100) DEFAULT NULL,  
  `course_id` varchar(50) NOT NULL,  
  `desc` varchar(250) NOT NULL,  
  `download_url` varchar(250) NOT NULL,  
  `out_ffmpeg` varchar(250) DEFAULT NULL,  
  `recordingId` varchar(140) NOT NULL,  
  `duration` varchar(100) NOT NULL,  
  PRIMARY KEY (`insertId`,`recordingId`)  
) ENGINE=InnoDB DEFAULT CHARSET=latin1  


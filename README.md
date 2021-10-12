# zoom_moodle_cloudfront_video_streaming
Embed ZOOM recordings into Moodle courses from repository with videos stored in AWS s3 bucket.


# Database table structure
+----------------+--------------+------+-----+---------+-------+
| Field          | Type         | Null | Key | Default | Extra |
+----------------+--------------+------+-----+---------+-------+
| insertId       | int(11)      | NO   | PRI | NULL    |       |
| start_time     | varchar(100) | YES  |     | NULL    |       |
| course_id      | varchar(50)  | NO   |     | NULL    |       |
| desc           | varchar(250) | NO   |     | NULL    |       |
| download_url   | varchar(250) | NO   |     | NULL    |       |
| out_ffmpeg     | varchar(250) | YES  |     | NULL    |       |
| recordingId    | varchar(140) | NO   | PRI | NULL    |       |
| duration       | varchar(100) | NO   |     | NULL    |       |
+----------------+--------------+------+-----+---------+-------+

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


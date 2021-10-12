# Embed ZOOM recordings into moodle courses from S3 bucket 

![ZOOM MOODLE diagram](/zoommoodle_flow.png)



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

# moodle/login/index.php simple patch

```//CLODFRONT PATCH

 /*Set-Cookie: 
 CloudFront-Policy=base64 encoded version of the policy statement; 
 Domain=optional domain name; 
 Path=/optional directory path; 
 Secure; 
 HttpOnly
 Set-Cookie: 
 CloudFront-Signature=hashed and signed version of the policy statement; 
 Domain=optional domain name; 
 Path=/optional directory path; 
 Secure; 
 HttpOnly
 Set-Cookie: 
 CloudFront-Key-Pair-Id=public key ID for the CloudFront public key whose corresponding private key you're using to generate the signature; 
 Domain=optional domain name; 
 Path=/optional directory path; 
 Secure; 
 HttpOnly 
 {
     "Statement": [
  {
      "Resource": "http://*",
      "Condition": {
   "IpAddress": {
       "AWS:SourceIp": "192.0.2.10/32"
   },
   "DateGreaterThan": {
       "AWS:EpochTime": 1357034400
   },
   "DateLessThan": {
       "AWS:EpochTime": 1357120800
   }
      }
  }
     ]
 } */

 $cfkeys_expires = time() + 86400;
 $cfkeys_policy = trim('{"Statement":[{"Resource":"https://s3bucket-xxxx.mydomain.com/*","Condition":{ "DateLessThan":{"AWS:EpochTime":'.$cfkeys_expires.'}}}]}');

 $cfkeys_signature = "";

 // load the private key
 $cfkeys_fp = fopen('/var/www/html/cloudfront_private_key.pem', "r");
 $cfkeys_priv_key = fread($cfkeys_fp, 8192);
 fclose($cfkeys_fp);
 $cfkeys_pkeyid = openssl_get_privatekey($cfkeys_priv_key);

 // compute signature
 openssl_sign($cfkeys_policy, $cfkeys_signature, $cfkeys_pkeyid);

 // free the key from memory
 openssl_free_key($cfkeys_pkeyid);

 setcookie('CloudFront-Policy', base64_encode($cfkeys_policy), $cfkeys_expires, "/", '.mydomain.com', true, false);
 setcookie('CloudFront-Signature', str_replace(array('+', '=', '/'), array('-', '_', '~'), base64_encode($cfkeys_signature)), $cfkeys_expires, "/", '.mydomain.com', true, false);
 setcookie('CloudFront-Key-Pair-Id', 'XXXXXXXXXXXXXX', $cfkeys_expires, "/", '.mydomain.com',  true, false);

 //CLOUDFRONT PATCH END```

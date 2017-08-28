<?PHP
/************************************************************************/
/* PHP CountMe v1.0                                                     */
/* ===========================                                          */
/*                                                                      */
/*   Written by Steve Dawson - http://www.stevedawson.com               */
/*   Freelance Web Developer - PHP, Perl and Javascript programming     */
/*                                                                      */
/* This program is free software. You can redistribute it and/or modify */
/************************************************************************/
## --  START OF CONFIG SECTION  --  ##
$counterstyle = "images";   # Enter images or text
$imagetype = "1";           # 1 to 10 = The type of image to display (SEE README FILE)
## --  END OF CONFIG SECTION  --  ##

$hitslog = "hits.txt";      # Path to the hits file, leave alone if in the same directory
$imagefolder = "digits";    # The full path to the images directory.
## Get the hitslog file ready
$hits = file($hitslog);
$hits = $hits[0] + 1;

## Opening the hits file and write the number of hits:
$fp = fopen($hitslog, "w");
fwrite($fp, $hits);

## Text counter, print the number of hits
if ($counterstyle == "text") { print $hits; }

## If Image Counter, get the required type and print them out.
if ($counterstyle == "images") {
 $digit = strval($hits);
 for ($i = 0; $i < strlen($hits); $i++) {
print "<img src=\"$imagefolder/$imagetype/$digit[$i].gif\" alt=\"There have been $hits visitors to this website\">";
                }
        }
## That's All Folks, more free simple scripts online at www.stevedawson.com
?>

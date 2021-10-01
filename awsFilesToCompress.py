# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime, timedelta

#å This python code writes the report generated that is used for identifying which images need to be reuploaded after compression
# It currently relies on manually initial output by running the following AWS CLI commands to get the data out
# aws s3 ls --summarize --human-readable --recursive s3://everfi-next/production/uploads/media/ >> output3.txt
# aws s3 ls --summarize --human-readable --recursive s3://everfi-custom-content >> output2.txt
# aws s3 ls --summarize --human-readable --recursive s3://everfi-custom-content/course-mod  >> output.txt
# to run these commands one needs to do it in shell having installed the aws cli
f = open("/Users/jpang/Documents/AWSimages/output2.txt", "r")
Lines = f.readlines()
f.close()
f = open("/Users/jpang/Documents/AWSimages/processedImages.txt", "r")
processedImages = f.readlines()
f.close()
f = open("/Users/jpang/Documents/AWSimages/awsresults.txt", "w")
# TODO: add in date filter
past = datetime.now() - timedelta(days=100)

count = 0
# Strips the newline character
totalSize = 0
for line in Lines:
    if "images" in line: #media is for Landing Pages images is for CM and coursemod
        date = line[0:19]
        dto = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').date()
        fileSize = line[22:30]
        actualFileSize = fileSize[0:4]
        if "MiB" in fileSize and dto > past.date():
            count += 1
            totalSize += float(actualFileSize)
            lineToWrite = line.strip()
            print line
            f.write(str(count) + " ")
            f.write(lineToWrite[21:])
            f.write("\n")
f.write("Total number of files: " + str(count))
f.write("\n")
f.write("Total Image Size of uncompressed images: " + str(totalSize))
f.write("\n")
f.write("Approximate Size of compressing images (assuming 80% compression): " + str((totalSize * .2)))
f.close()

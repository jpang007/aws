from PIL import Image
import os
import sys
import glob
import boto3
import filecmp
import math
import pathlib
from shutil import copyfile
from os import listdir
from os.path import isfile, join

### This code does all the heavy handling of using the awsresults.txt generated from awsFilesToCompress
### to download, compress, delete the old existing file out of AWS S3, then reupload the compressed version

s3 = boto3.resource('s3')
bucket = 'everfi-custom-content'

def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start

def download_s3_folder(bucket_name, s3_folder, local_dir=None):
    """
    Download the contents of a folder directory
    Args:
        bucket_name: the name of the s3 bucket
        s3_folder: the folder path in the s3 bucket
        local_dir: a relative or absolute directory path in the local file system
    """
    bucket = s3.Bucket(bucket_name)
    for obj in bucket.objects.filter(Prefix=s3_folder):
        target = obj.key if local_dir is None \
            else os.path.join(local_dir, os.path.relpath(obj.key, s3_folder))
        if not os.path.exists(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))
        if obj.key[-1] == '/':
            continue
        #for filtering out downloaded files by size
        if obj.size < 1000000:
            continue
        print (obj.size)
        bucket.download_file(obj.key, target)

def delete_s3_objects(bucket_name, s3_folder):
    bucket = s3.Bucket(bucket_name)
    for obj in bucket.objects.filter(Prefix=s3_folder):
        s3.Object(bucket.name,obj.key).delete()

def create_s3_folder(bucket_name, s3_folder):
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket_name, Key=(s3_folder+'/'))

def upload_s3_file(filename, bucket_name, s3_folder,awsFileName):
    s3.meta.client.upload_file(filename, bucket_name, s3_folder+'/'+awsFileName, ExtraArgs={"ACL": "public-read", "ContentType": "image/jpeg"})

def copy_local_files(filePath):
    localPath = os.getcwd()
    localPath = localPath + '/' + filePath
    compressedFilePath = '/Users/jpang/Documents/compressedAWSImages/' + filePath
    result = filecmp.dircmp(localPath, compressedFilePath)
    uncopiedFiles = (list(set(result.left_list) - set(result.right_list)))
    for i in uncopiedFiles:
        print ("copying over files that weren't compressed" + i)
        source = localPath + '/' + i
        destination = compressedFilePath + '/' + i
        copyfile(source,destination)

def compressMe(file, cwd, path, verbose = False):
      # Get the path of the file
    print('compressing', file)

    filepath = os.path.join(cwd,
                            file)

    # open the image
    # we only want to compress big files so skip anything < 100KB
    size = os.path.getsize('/Users/jpang/Documents/AWSImages/'+path+file)
    if size > 100000:
        picture = Image.open(filepath)
        #resize image
        #we only want to resize large images
        currentSize = picture.size
        flag = False
        if currentSize[0] > 4000:
            flag = True
            newWidth = currentSize[0] * .25
            newHeight = currentSize[1] * .25
        elif currentSize[0] > 2000:
            flag = True
            newWidth = currentSize[0] * .5
            newHeight = currentSize[1] * .5
        elif currentSize[0] > 1500:
            flag = True
            newWidth = currentSize[0] * .7
            newHeight = currentSize[1] * .7
        if (flag == True):
            picture = picture.resize((math.floor(newWidth), math.floor(newHeight)))
        # Compress image, based on jpeg or png
        file_extension = pathlib.Path('/Users/jpang/Documents/AWSImages/'+path+file).suffix
        if file_extension == '.jpg' or file_extension == '.jpeg':
            picture.save('/Users/jpang/Documents/compressedAWSImages/'+path+file, format='JPEG', optimize = True, quality=85)
        if file_extension == '.png':
            picture.save('/Users/jpang/Documents/compressedAWSImages/'+path+file, format='PNG', optimize = True, quality=85)

    return

verbose = False

# checks for verbose flag
if (len(sys.argv)>1):

    if (sys.argv[1].lower()=="-v"):
        verbose = True


formats = ('.jpg', '.jpeg', '.png')
# download s3 files first
# need to parse the awsresults
f = open("/Users/jpang/Documents/AWSimages/awsresults.txt", "r")
Lines = f.readlines()
listOfImageFolders = []

for line in range(0,len(Lines) - 3):
    line = str(Lines[line])
    line = line[12:]
    endOfLine = (find_nth(line,'/',3)) #MUST EDIT BASED ON HOW MANY / THERE ARE
    line = line[:endOfLine].strip()
    listOfImageFolders.append(line)

listOfImageFolders = list(set(listOfImageFolders))
print("downloading images")
print (listOfImageFolders)
for i in listOfImageFolders:
    print (i)
    download_s3_folder('everfi-custom-content',i) #everfi-custom-content (Custom Moments) everfi-next (Landing Pages)

# looping through all the files
# in a current directory
fileToPathTo = '/Users/jpang/Documents/compressedAWSImages'

for i in listOfImageFolders:
    cwd = os.getcwd()
    cwd = cwd + '/' + i
    print (cwd)
    #if directory doesn't exist
    newPath = os.path.join(fileToPathTo, i)
    if (os.path.isdir(newPath) == False):
        os.makedirs(newPath)

    for file in os.listdir(cwd):
        print (file)
        checkFile = fileToPathTo + "/" + i + "/" + file
        # print (checkFile)
        if (os.path.isfile(checkFile) == False):
            if os.path.splitext(file)[1].lower() in formats:
                compressMe(file, cwd, i + '/', verbose)

    #compare to original folder and copy over any photos that were not compressed
    copy_local_files(i)

    # delete old photo out of S3
    print ("deleting old photos for: " + i)
    # delete_s3_objects(bucket, i)

    # create new folder for images
    print ("creating new folder for: " + i)
    # create_s3_folder(bucket, i)

    pathname = '/Users/jpang/Documents/compressedAWSImages/'
    awsDirection = pathname + i
    onlyfiles = [f for f in listdir(awsDirection) if isfile(join(awsDirection, f))]
    # upload new compressed photo into S3
    print ("uploading new images for: " + i)
    for j in onlyfiles:
        compressedImagePath = awsDirection + '/' + j
        print ("replacing image: " + j)
        # upload_s3_file(compressedImagePath, bucket, i, j)

print("Done")

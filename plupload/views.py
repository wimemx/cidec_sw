import os
import datetime
import random
import string
import json

from django.http import HttpResponse, Http404
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response

#Directory where you want to save your files
FILE_FOLDER = "templates/static/media/csv_files/"


def upload(request):
    if request.method == "POST":
        # Do any other process once you have upoloaded you files
        print "post"
    template_vars_template = RequestContext(request)
    return render_to_response('upload_form.html',
                              template_vars_template)


def upload_custom(request):
    if request.method == "POST":
        # Do any other process once you have upoloaded you files
        print "post"
    #I'm using a dir with today date as name,
    #so i send the constructed url for the latest file load
    #and for the delete file url
    todays_date = datetime.datetime.now().strftime("%Y/%m/%d/")
    print todays_date
    url_get_last = "/get_files/"+todays_date
    delete_file_url = "/del_file/"+todays_date
    media_folder = "/static/media/csv_files/"+todays_date
    all_files_url = "/get_all_files/"+todays_date
    template_vars = dict(url_get_last=url_get_last,
                         delete_file_url=delete_file_url,
                         media_folder=media_folder,
                         all_files_url=all_files_url)
    template_vars_template = RequestContext(request, template_vars)
    return render_to_response('custom_queue.html',
                              template_vars_template)


def upload_file(request):
    if request.method == 'POST' and request.FILES:
        dir_name = str(datetime.date.today())
        dir_fd = os.open(os.path.join(settings.PROJECT_PATH,
                                      FILE_FOLDER),
                         os.O_RDONLY)
        os.fchdir(dir_fd)
        #creates a directory named to today's date
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        os.chdir(dir_name)

        for _file in request.FILES:
            handle_uploaded_file(request.FILES[_file], "csv")
        os.close(dir_fd)
        #response only to notify plUpload that the upload was successful
        return HttpResponse()
    else:
        raise Http404


def handle_uploaded_file(f, ext):
    """
    Here you can do whatever you like with your files, like resize them if they
    are images
    :param f: the file
    :param ext: extention to append in the file name
    """
    filelist = os.listdir(os.getcwd())
    filelist = filter(lambda x: not os.path.isdir(x), filelist)

    filelist.sort(reverse=True)
    if not filelist[0].startswith("."):
        try:
            file_n = str(int(filelist[0].split(".")[0])+1)
        except ValueError:
            file_n = "1000"
    else:
        file_n = "1000"
    print file_n
    file_n += "." + ext
    with open(file_n, 'wb+') as destination:
        print "chunks", f.chunks()
        for chunk in f.chunks():
            destination.write(chunk)


def get_files(request, year, month, day):
    dir_name = str.join("-", [year, month, day])
    dir_path = os.path.join(settings.PROJECT_PATH, FILE_FOLDER)
    dir_fd = os.open(dir_path+dir_name, os.O_RDONLY)
    os.fchdir(dir_fd)
    filelist = os.listdir(os.getcwd())
    filelist = filter(lambda x: not os.path.isdir(x), filelist)
    print filelist
    filelist.sort(reverse=True)
    print filelist[0]
    #newest = max(filelist, key=lambda x: os.stat(x).st_mtime)
    os.close(dir_fd)
    return HttpResponse(content=filelist[0], status=200,
                        mimetype="text/plain")


def del_file(request, year, month, day):
    if 'file' in request.GET:
        dir_name = str.join("-", [year, month, day])
        dir_path = os.path.join(settings.PROJECT_PATH, FILE_FOLDER)
        files = os.listdir(dir_path+dir_name)
        dir_fd = os.open(dir_path+dir_name, os.O_RDONLY)
        os.fchdir(dir_fd)

        for _file in files:
            if str(_file) == request.GET['file']:
                os.remove(_file)
        os.close(dir_fd)
        result = 1
    else:
        result = 0
    return HttpResponse(result)


def get_all_files(request, year, month, day):
    dir_name = str.join("-", [year, month, day])
    dir_path = os.path.join(settings.PROJECT_PATH, FILE_FOLDER)
    dir_fd = os.open(dir_path+dir_name, os.O_RDONLY)
    os.fchdir(dir_fd)
    filelist = os.listdir(os.getcwd())
    filelist = filter(lambda x: not os.path.isdir(x), filelist)
    files = []
    for file_ in filelist:
        if not file_.startswith("."):
            files.append(dict(name=file_.split(".")[0], filename=file_))
    return HttpResponse(content=json.dumps(files), status=200,
                        mimetype="application/json")
FROM ubuntu:16.04
MAINTAINER Dmitry Veselov <d.a.veselov@yandex.ru>

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y libffi-dev libmagic-dev libmagickwand-dev
RUN apt-get install -y libreoffice libreofficekit-dev
RUN apt-get install -y python3-dev python3-pip git

RUN apt-get clean && apt-get -y update && apt-get install -y locales && locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

ADD . /home/docsbox
WORKDIR /home/
RUN pip3 install --upgrade pip
RUN pip3 install -r docsbox/requirements.txt

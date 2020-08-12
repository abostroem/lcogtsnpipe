FROM i386/python:2.7.18-slim-stretch

ENV iraf /iraf/iraf/
ENV IRAFARCH linux

RUN apt-get update \
        && apt -y install gcc make flex git \
        && apt -y install libcurl4-openssl-dev libexpat-dev libreadline-dev gettext\
        && apt-get autoclean \
        && rm -rf /var/lib/apt/lists/*

RUN mkdir -p $iraf \
        && cd /iraf \
        && git clone https://github.com/iraf-community/iraf.git \
        && cd $iraf \
        && git checkout ba22d13 \
        && ./install < /dev/null \
        && make $IRAFARCH \
        && make sysgen

RUN apt-get update \
        && apt-get -y install libx11-dev libcfitsio-bin wget x11-apps libtk8.6 sextractor procps g++ \
        mysql-client libmariadbclient-dev openssh-client wcstools libxml2 vim libssl1.0.2 zip pkg-config \
        libpng-dev libfreetype6-dev \
        && apt-get autoclean \
        && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/sextractor /usr/bin/sex

RUN pip install cryptography==2.4.1 numpy>=1.12 astropy matplotlib==2.2.5 pyraf mysql-python scipy astroquery==v0.4 statsmodels==0.10 cython

RUN pip install git+git://github.com/kbarbary/sep.git@master git+git://github.com/dguevel/PyZOGY.git && rm -rf ~/.cache/pip

RUN wget http://ds9.si.edu/download/debian9/ds9.debian9.8.0.1.tar.gz \
        && tar -xzvf ds9.debian9.8.0.1.tar.gz -C /usr/local/bin \
        && rm -rf ds9.debian9.8.0.1.tar.gz

RUN wget http://cdsarc.u-strasbg.fr/ftp/pub/sw/cdsclient.tar.gz \
        && tar -xzvf cdsclient.tar.gz -C /usr/src && rm cdsclient.tar.gz \
        && cd /usr/src/cdsclient-* && ./configure && make && make install

ENV LCOSNPIPE /lcogtsnpipe
ENV DISPLAY host.docker.internal:0

RUN mkdir -p /home/supernova/iraf && /usr/sbin/groupadd -g 20000 "domainusers" \
        && /usr/sbin/useradd -g 20000 -d /home/supernova -M -N -u 10197 supernova \
        && chown -R supernova:domainusers /home/supernova \
        && mkdir -p $LCOSNPIPE

RUN chown -R supernova:domainusers $LCOSNPIPE /usr/local

USER supernova

COPY . $LCOSNPIPE

WORKDIR $LCOSNPIPE/trunk

RUN python setup.py build -f && python setup.py install -f

WORKDIR /home/supernova/iraf

RUN mkiraf --term=xgterm -i

WORKDIR /home/supernova

ENTRYPOINT /bin/bash

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  ia.cecil
#  
#  Copyleft 2012-2022 Iuri Guilherme <https://iuri.neocities.org/>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  

### Arguments explanation
### Usage: start.py log_level mode bots port host reload canonical
### Defaults: start.py info quart iacecil 8000 127.0.0.1 True None
###
### log_level: Used in the logging module globally, this included 
### imported libraries where applicable;
###
### mode: One of the pre defined modes of operation in the main routine 
### at start.py. This is done because different mode of operation 
### require different settings. For example supporting long polling and 
### webhooks would require a huge rewrite everytime so it's easier to 
### set up such running environments in one single file. Also 
### development and production setups are not always a matter of 
### running quart on development mode, but this wrapper (start.py) 
### should take care of everything to make it simple to run easily in 
### whichever settings;
###
### bots: This would be an alias (or a comma separated list of aliases) 
### for bots already configured at instance/config.py. This allows for 
### selection of which bot tokens will be used simultaneously in an 
### environment where they should be selected before the script starts 
### such as all bots running in long polling mode.
###
### port: TCP port for uvicorn/quart binding;
###
### host: fqdn, ipv4 or localhost hostname for uvicorn/quart binding;
###
### reload: uvicorn specific development option;
###
### canonical: (currently unused) gambiarra to make routes work in 
### subdirectories. Spoiler alert: it never worked;
###

### This file exists and it's expected to have dozens of lines because 
### this software has been historically been rewritten from scratch to 
### support / test / experiment with multiple technologies while not 
### breaking old versions of the running scripts. It is desirable to 
### add new controllers at iacecil/controllers and import them from 
### this file / command line calling than to refactor all code to force 
### the whole software to stick to one way of working. This versatility 
### feature comes from years of experience rewriting thousands of lines 
### of code, also inspired by plugin based similar software which in 
### itself probably has yet more decades of experience. So if you think 
### you have a better idea or feel an urge to "clean up" by removing 
### unused ancient code, fork the repository and have fun.

try:
    if __name__ == '__main__':
        import asyncio, iacecil, locale, logging, sys, uvicorn
        # ~ locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
        log_level = 'info'
        if len(sys.argv) > 1:
            log_level = sys.argv[1]
        else:
            logger.warning(u"""Logging level not informed, assuming {}\
""".format(log_level))
        logging.basicConfig(level = getattr(logging, log_level.upper()))
        logger = logging.getLogger(iacecil.name)
        
        ### Default args
        bots = 'iacecil'
        mode = 'quart'
        port = 8000
        host = '127.0.0.1'
        log_level = 'info'
        reload = True
        canonical = None
        skip_intro = False
        log_messages = True
        personas = 'default'
        add_startswith = None
        add_endswith = None
        text = None
        
        ### Args parsing
        if len(sys.argv) > 2:
            mode = sys.argv[2]
            logger.info(u"Setting operation MODE to {}".format(
                mode)
            )
            if mode in ['polly']:
                text = sys.argv[3:]
                logger.info(u"Setting TEXT to {}".format(text))
            elif len(sys.argv) > 3:
                bots = sys.argv[3]
                logger.info(u"""Using configuration from BOTS "{}" f\
rom config file.""".format(bots))
                if mode in ['fpapagaio']:
                    if len(sys.argv) > 4:
                        skip_intro = bool(sys.argv[4])
                        logger.info(u"Setting SKIP_INTRO to {}".format(
                            str(skip_intro))
                        )
                elif mode in ['fpersonas']:
                    if len(sys.argv) > 4:
                        personas = sys.argv[4]
                        logger.info(u"Setting PERSONAS to {}".format(
                            str(personas))
                        )
                        if len(sys.argv) > 5:
                            skip_intro = bool(sys.argv[5])
                            logger.info(
                                u"Setting SKIP_INTRO to {}".format(
                                str(skip_intro))
                            )
                            if len(sys.argv) > 6:
                                log_messages = bool(sys.argv[6])
                                logger.info(u"""Setting LOG_MESSAGES to\
 {}""".format(str(log_messages)))
                                if len(sys.argv) > 7:
                                    add_startswith = sys.argv[7]
                                    logger.info(u"""Setting ADD_STARTSW\
ITH to {}""".format(str(add_startswith)))
                                    if len(sys.argv) > 8:
                                        add_endswith = sys.argv[8]
                                        logger.info(u"""Setting ADD_END\
SWITH to {}""".format(str(add_endswith)))
                else:
                    if len(sys.argv) > 4:
                        port = sys.argv[4]
                        logger.info(u"Setting PORT to {}".format(port))
                        if len(sys.argv) > 5:
                            host = sys.argv[5]
                            logger.info(u"Setting HOST to {}".format(
                                str(host))
                            )
                            if len(sys.argv) > 6:
                                reload = bool(sys.argv[6])
                                logger.info(
                                    u"Setting RELOAD to {}".format(
                                    str(reload))
                                )
                                if len(sys.argv) > 7:
                                    canonical = str(sys.argv[7])
                                    logger.info(u"""Setting CANONICAL t\
o {}""".format(str(canonical)))
            else:
                logger.warning(u"BOTS names not informed, assuming {}\
                    ".format(bots))
        else:
            logger.warning(
                u"Operation MODE not informed, assuming {}".format(
                    mode)
            )
        ### Running scripts
        if mode == 'quart':
            try:
                logger.info(u"Starting {}".format(iacecil.actual_name))
                app = iacecil.get_app(bots.split(','))
                setattr(app, 'canonical', canonical)
                uvicorn.run(
                    app,
                    host = host,
                    port = int(port),
                    log_level = log_level,
                )
                logger.info(u"Finishing {}".format(iacecil.actual_name))
            except Exception as e:
                logger.critical(repr(e))
                logger.warning(u"Finishing with error {}...\
                ".format(iacecil.actual_name))
                raise
        elif mode == 'furhat':
            try:
                logger.info(u"Starting {}".format(iacecil.actual_name))
                app = iacecil.get_app(bots.split(','))
                setattr(app, 'furhat', True)
                uvicorn.run(
                    app,
                    host = host,
                    port = int(port),
                    log_level = log_level,
                )
                logger.info(u"Finishing {}".format(iacecil.actual_name))
            except Exception as e:
                logger.critical(repr(e))
                logger.warning(u"Finishing with error {}...\
                ".format(iacecil.actual_name))
                raise
        elif mode == 'socket':
            try:
                logger.info(u"Starting {}".format(iacecil.actual_name))
                app = iacecil.get_app(bots.split(','))
                setattr(app, 'canonical', canonical)
                uvicorn.run(
                    app,
                    uds = 'uvicorn.sock',
                    forwarded_allow_ips = '*',
                    proxy_headers = True,
                    timeout_keep_alive = 0,
                    log_level = log_level,
                )
                logger.info(u"Finishing {}".format(iacecil.actual_name))
            except Exception as e:
                logger.critical(repr(e))
                logger.warning(u"Finishing with error {}...\
                ".format(iacecil.actual_name))
                raise
        elif mode == 'fpapagaio':
            try:
                logger.info(u"Starting {}".format(iacecil.actual_name))
                from iacecil.controllers.furhat_bot.papagaio import \
                    papagaio
                asyncio.run(papagaio(
                    bots.split(',')[0],
                    skip_intro,
                ))
                logger.info(u"Finishing {}".format(iacecil.actual_name))
            except Exception as exception:
                logger.critical(repr(exception))
                logger.warning(u"Finishing with error {}...".format(
                    iacecil.actual_name)
                )
                raise
        elif mode == 'fpersonas':
            try:
                logger.info(u"Starting {}".format(iacecil.actual_name))
                from iacecil.controllers.furhat_bot.personas import \
                    personas
                asyncio.run(personas(
                    personas.split(','),
                    skip_intro = skip_intro,
                    log_messages = log_messages,
                    add_startswith = add_startswith,
                    add_endswith = add_endswith,
                ))
                logger.info(u"Finishing {}".format(iacecil.actual_name))
            except Exception as exception:
                logger.critical(repr(exception))
                logger.warning(u"Finishing with error {}...".format(
                    iacecil.actual_name)
                )
                raise
        elif mode == 'block':
            try:
                logger.info(u"Starting {}".format(iacecil.actual_name))
                app = iacecil.get_app(bots.split(','))
                setattr(app, 'canonical', canonical)
                iacecil.run_app(app)
                logger.info(u"Finishing {}".format(iacecil.actual_name))
            except Exception as e:
                logger.critical(repr(e))
                logger.warning(u"Finishing with error {}...\
                ".format(iacecil.actual_name))
                raise
        elif mode == 'dev':
            try:
                logger.info(u"Starting {}".format(iacecil.actual_name))
                uvicorn.run(
                    'iacecil:app',
                    host = host,
                    port = int(port),
                    log_level = log_level,
                    reload = reload,
                )
                logger.info(u"Finishing {}".format(iacecil.actual_name))
            except Exception as e:
                logger.critical(repr(e))
                logger.warning(u"Finishing with error {}...\
                ".format(iacecil.actual_name))
                raise
        elif mode == 'polly':
            try:
                logger.info(u"Starting {}".format(iacecil.actual_name))
                from iacecil.controllers import amazon_boto
                print(u"\n\nFile is: {}\n\n".format(asyncio.run(
                    amazon_boto.get_audio(
                        Text = ' '.join(text),
                        LanguageCode = 'pt-BR',
                        VoiceId = 'Camila',
                        # ~ OutputFormat = 'pcm',
                        Engine = 'neural',
                        # ~ Extension = 'wav',
                    )
                )))
                logger.info(u"Finishing {}".format(iacecil.actual_name))
            except Exception as exception:
                logger.critical(repr(exception))
                logger.warning(u"Finishing with error {}...".format(
                    iacecil.actual_name)
                )
                raise
        elif mode == 'loop':
            try:
                logger.info(u"Starting {}".format(iacecil.actual_name))
                from iacecil.controllers.aiogram_bot import (
                    aiogram_startup,
                )
                config = None
                try:
                    from instance.config import Config
                    config = Config()
                except Exception as e1:
                    logger.critical(u"""{} config file not found or som\
ehow wrong. RTFM.\n{}""".format(actual_name, str(e1)))
                    raise
                dispatchers = aiogram_startup(config.bots,
                    bots.split(','))
                loop = None
                try:
                    loop = asyncio.get_event_loop()
                except Exception as e2:
                    logger.debug(repr(e2))
                    try:
                        loop = asyncio.new_event_loop()
                    except Exception as e3:
                        logger.debug(repr(e3))
                for dispatcher in dispatchers:
                    loop.create_task(dispatcher.start_polling(
                        reset_webhook = True,
                        timeout = 20,
                        relax = 0.1,
                        fast = True,
                        allowed_updates = None,
                    ))
                try:
                    loop.run_forever()
                except KeyboardInterrupt:
                    try:
                        for dispatcher in dispatchers:
                            loop.call_soon(dispatcher.storage.close())
                            loop.call_soon(
                                dispatcher.storage.wait_closed())
                        loop.stop()
                        logger.info('done')
                    except Exception as e4:
                        logger.debug(repr(e4))
                        raise
                except Exception as e5:
                    logger.debug(repr(e5))
                logger.info(u"Finishing {}".format(iacecil.actual_name))
            except Exception as e:
                logger.critical(repr(e))
                logger.warning(u"Finishing with error {}...\
                ".format(iacecil.actual_name))
                raise
        else:
            logger.info(u"""Wrong operation mode. RTFM will you please.\
 Bye.""")
except Exception as exception:
    print(u"RTFM")
    print(repr(exception))
    raise

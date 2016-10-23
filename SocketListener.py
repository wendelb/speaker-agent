import logging
import os
import socket
import sys
import threading
from SpeakerActor import Speakers

socket_filename = 'socket'
socket_folder   = '/run/speakers'

class SocketListener(object):
    """description of class"""

    def __init__(self):
        self.logger = logging.getLogger('SpeakerAgent.SocketListener')
        try:
            os.makedirs(socket_folder, exist_ok=True)
        except:
            self.logger.fatal( "Unexpected error during initialization (ensure paths): %s" % sys.exc_info()[0])
            sys.exit(11)

        try:
            if os.path.exists(socket_folder + '/' + socket_filename):
                os.remove(socket_folder + '/' + socket_filename)
        except:
            self.logger.fatal("Unexpected error during initialization (cleanup stage): %s" % sys.exc_info()[0])
            sys.exit(12)

    def run(self):
        th = threading.Thread(target=self._threadWaitForConnection,args=())
        th.start()

    def _threadClient(self, conn):
        conn.send(str.encode('This is speakers\n'))
        acquired = False
        try:
            data = conn.recv(128)
            input = data.decode("utf-8")

            # Expected: 'This is [Name]\n'
            if not ((input[:8] == 'This is ') and (input[-1] == '\n')):
                conn.sendall('Wrong syntax. "This is [Name]" expected\n'.encode())
                raise ValueError()

            name = input[8:-1]
            self.logger.info("New client connected: {}".format(name))
            conn.sendall('{}, we are ready for you\n'.format(name).encode())

            while True:
                data = conn.recv(128)

                if not data:
                    break

                input = data.decode('utf-8')[:-1]
                if not ((input == 'acquire') or (input == 'release') or (input == 'quit')):
                    conn.sendall('Wrong syntax. Only "acquire", "release" and "quit" are supported\n'.encode())
                    break

                if (input == 'quit'):
                    break

                if (input == 'acquire'):
                    if not acquired:
                        acquired = True
                        Speakers.addDevice('socket-' + name)
                        self.logger.info('Session acquired by {}'.format(name))
                        conn.sendall('acquired\n'.encode())
                    else:
                        conn.sendall('Already acquired\n'.encode())

                if (input == 'release'):
                    if acquired:
                        acquired = False
                        Speakers.removeDevice('socket-' + name)
                        self.logger.info('Session released by {}'.format(name))
                        conn.sendall('released\n'.encode())
                    else:
                        conn.sendall('No session found that can be released\n'.encode())


        finally:
            conn.close()

            if acquired:
                Speakers.removeDevice('socket-' + name)
                self.logger.info('Session released as the connection to {} was closed'.format(name))


    def _threadWaitForConnection(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            s.bind(socket_folder + '/' + socket_filename)
        except socket.error as e:
            self.logger.fatal("Unexpected error during initialization (binding): %s" % e)
            sys.exit(13)

        s.listen(5)
        self.logger.debug('Socket is up')
        os.chmod(socket_folder + '/' + socket_filename, 0o666)

        while True:
            conn, addr = s.accept()
            self.logger.info('A new client has connected')

            threading.Thread(target=self._threadClient,args=(conn,)).start()
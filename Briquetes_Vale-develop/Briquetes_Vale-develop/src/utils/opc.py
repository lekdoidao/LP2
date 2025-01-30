# OPC - Open Process Control
from opcua import Client, ua
import OpenOPC
import time
import logging

class OPCUAWriter:
    def __init__(self, server_url, node_id):
        self.server_url = server_url
        self.node_id = node_id
        self.client = None
        self.logger = logging.getLogger('opc_ua_writer')

    def connect(self):
        """Conecta ao servidor OPC UA"""
        try:
            self.client = Client(self.server_url)
            self.client.connect()
            self.logger.info(f"Conectado ao servidor OPC UA: {self.server_url}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao conectar ao servidor OPC UA: {str(e)}")
            return False

    def write_value(self, value):
        """Escreve valor na tag especificada"""
        try:
            if self.client is None:
                if not self.connect():
                    return False

            node = self.client.get_node(self.node_id)
            dv = ua.DataValue(ua.Variant(value, ua.VariantType.Float))
            node.set_value(dv)
            self.logger.info(f"Valor {value} escrito com sucesso na tag {self.node_id}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao escrever valor via OPC UA: {str(e)}")
            return False

    def disconnect(self):
        """Desconecta do servidor"""
        if self.client:
            self.client.disconnect()
            self.logger.info("Desconectado do servidor OPC UA")

class OPCDAWriter:
    def __init__(self, server_name, tag_name):
        self.server_name = server_name
        self.tag_name = tag_name
        self.client = None
        self.logger = logging.getLogger('opc_da_writer')

    def connect(self):
        """Conecta ao servidor OPC DA"""
        try:
            self.client = OpenOPC.client()
            self.client.connect(self.server_name)
            self.logger.info(f"Conectado ao servidor OPC DA: {self.server_name}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao conectar ao servidor OPC DA: {str(e)}")
            return False

    def write_value(self, value):
        """Escreve valor na tag especificada"""
        try:
            if self.client is None:
                if not self.connect():
                    return False

            self.client.write((self.tag_name, value))
            self.logger.info(f"Valor {value} escrito com sucesso na tag {self.tag_name}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao escrever valor via OPC DA: {str(e)}")
            return False

    def disconnect(self):
        """Desconecta do servidor"""
        if self.client:
            self.client.close()
            self.logger.info("Desconectado do servidor OPC DA")
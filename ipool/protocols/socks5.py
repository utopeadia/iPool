import asyncio
import logging
import socket
import struct
from typing import Optional, Tuple

from ipool.protocols.base import ProxyServer
from ipool.node.models import ProxyNode

logger = logging.getLogger(__name__)

# SOCKS5 常量
SOCKS_VER = 0x05
SOCKS_AUTH_NONE = 0x00
SOCKS_AUTH_USERNAME_PASSWORD = 0x02
SOCKS_CMD_CONNECT = 0x01
SOCKS_ATYP_IPV4 = 0x01
SOCKS_ATYP_DOMAINNAME = 0x03
SOCKS_ATYP_IPV6 = 0x04

# SOCKS5 响应码
SOCKS_SUCCESS = 0x00
SOCKS_GENERAL_FAILURE = 0x01
SOCKS_CONNECTION_NOT_ALLOWED = 0x02
SOCKS_NETWORK_UNREACHABLE = 0x03
SOCKS_HOST_UNREACHABLE = 0x04
SOCKS_CONNECTION_REFUSED = 0x05
SOCKS_TTL_EXPIRED = 0x06
SOCKS_COMMAND_NOT_SUPPORTED = 0x07
SOCKS_ADDRESS_TYPE_NOT_SUPPORTED = 0x08


class Socks5Server(ProxyServer):
    """SOCKS5 代理服务器实现"""
    
    async def _create_server(self):
        """创建SOCKS5服务器"""
        return await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
    
    async def _run_server(self):
        """运行SOCKS5服务器"""
        async with self.server:
            await self.server.serve_forever()
    
    async def handle_client(self, reader, writer):
        """处理SOCKS5客户端连接"""
        client_addr = writer.get_extra_info('peername')
        logger.debug(f"新的客户端连接: {client_addr}")
        
        try:
            # 验证方法协商
            if not await self._handle_auth_negotiation(reader, writer):
                return
            
            # 处理客户端请求
            if not await self._handle_client_request(reader, writer):
                return
            
            # 获取代理节点
            proxy_node = await self.get_proxy()
            if not proxy_node:
                logger.error("没有可用的代理节点")
                await self._send_reply(writer, SOCKS_GENERAL_FAILURE)
                return
            
            # 建立与目标服务器的连接并转发流量
            await self._handle_proxy_connection(reader, writer, proxy_node)
            
        except (asyncio.IncompleteReadError, ConnectionError) as e:
            logger.debug(f"连接错误: {str(e)}")
        except Exception as e:
            logger.error(f"处理客户端时出错: {str(e)}", exc_info=True)
        finally:
            writer.close()
            await writer.wait_closed()
            logger.debug(f"客户端连接关闭: {client_addr}")
    
    async def _handle_auth_negotiation(self, reader, writer) -> bool:
        """处理SOCKS5认证协商"""
        try:
            # 接收客户端认证方法
            ver, nmethods = struct.unpack('!BB', await reader.readexactly(2))
            if ver != SOCKS_VER:
                logger.warning(f"不支持的SOCKS版本: {ver}")
                return False
            
            methods = await reader.readexactly(nmethods)
            
            # 目前只支持无认证模式
            if SOCKS_AUTH_NONE not in methods:
                # 发送不支持的认证方法响应
                writer.write(struct.pack('!BB', SOCKS_VER, 0xFF))
                await writer.drain()
                logger.warning("客户端不支持无认证模式")
                return False
            
            # 发送选择无认证模式的响应
            writer.write(struct.pack('!BB', SOCKS_VER, SOCKS_AUTH_NONE))
            await writer.drain()
            return True
            
        except Exception as e:
            logger.error(f"认证协商失败: {str(e)}")
            return False
    
    async def _handle_client_request(self, reader, writer) -> bool:
        """处理SOCKS5客户端请求"""
        try:
            # 解析客户端请求
            ver, cmd, rsv, atyp = struct.unpack('!BBBB', await reader.readexactly(4))
            
            if ver != SOCKS_VER:
                logger.warning(f"不支持的SOCKS版本: {ver}")
                return False
            
            if cmd != SOCKS_CMD_CONNECT:
                logger.warning(f"不支持的SOCKS命令: {cmd}")
                await self._send_reply(writer, SOCKS_COMMAND_NOT_SUPPORTED)
                return False
            
            # 解析目标地址
            target_addr, target_port = await self._parse_target_address(reader, atyp)
            if not target_addr:
                await self._send_reply(writer, SOCKS_ADDRESS_TYPE_NOT_SUPPORTED)
                return False
            
            logger.debug(f"目标连接请求: {target_addr}:{target_port}")
            
            # 发送成功响应
            await self._send_reply(writer, SOCKS_SUCCESS)
            return True
            
        except Exception as e:
            logger.error(f"处理客户端请求失败: {str(e)}")
            try:
                await self._send_reply(writer, SOCKS_GENERAL_FAILURE)
            except:
                pass
            return False
    
    async def _parse_target_address(self, reader, atyp) -> Tuple[Optional[str], int]:
        """解析目标地址和端口"""
        if atyp == SOCKS_ATYP_IPV4:
            # IPv4地址
            addr_bytes = await reader.readexactly(4)
            addr = socket.inet_ntop(socket.AF_INET, addr_bytes)
        elif atyp == SOCKS_ATYP_DOMAINNAME:
            # 域名
            addr_len = (await reader.readexactly(1))[0]
            addr = (await reader.readexactly(addr_len)).decode('utf-8')
        elif atyp == SOCKS_ATYP_IPV6:
            # IPv6地址
            addr_bytes = await reader.readexactly(16)
            addr = socket.inet_ntop(socket.AF_INET6, addr_bytes)
        else:
            logger.warning(f"不支持的地址类型: {atyp}")
            return None, 0
        
        # 读取端口号
        port_bytes = await reader.readexactly(2)
        port = struct.unpack('!H', port_bytes)[0]
        
        return addr, port
    
    async def _send_reply(self, writer, status):
        """发送SOCKS5响应"""
        # 构造响应: VER | REP | RSV | ATYP | BND.ADDR | BND.PORT
        # 使用通用的本地绑定地址 0.0.0.0:0
        response = struct.pack('!BBBB', SOCKS_VER, status, 0, SOCKS_ATYP_IPV4)
        response += socket.inet_aton('0.0.0.0')  # BND.ADDR
        response += struct.pack('!H', 0)  # BND.PORT
        
        writer.write(response)
        await writer.drain()
    
    async def _handle_proxy_connection(self, client_reader, client_writer, proxy_node: ProxyNode):
        """处理代理连接和数据转发"""
        # 此处应包含通过目标代理节点建立连接的逻辑
        # 简单起见，这里仅展示基本框架
        target_addr = writer.get_extra_info('target_addr')
        target_port = writer.get_extra_info('target_port')
        
        logger.info(f"使用代理节点 {proxy_node.host}:{proxy_node.port} 连接到目标 {target_addr}:{target_port}")
        
        try:
            # 创建与代理的连接
            proxy_reader, proxy_writer = await asyncio.open_connection(
                proxy_node.host, proxy_node.port
            )
            
            # 双向转发数据
            await asyncio.gather(
                self._transfer_data(client_reader, proxy_writer),
                self._transfer_data(proxy_reader, client_writer)
            )
        except Exception as e:
            logger.error(f"代理连接失败: {str(e)}")
        finally:
            proxy_writer.close()
            await proxy_writer.wait_closed()
    
    async def _transfer_data(self, reader, writer):
        """在两个连接之间传输数据"""
        try:
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except Exception as e:
            logger.debug(f"数据传输错误: {str(e)}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass


import asyncio
import logging
import re
from urllib.parse import urlparse

from ipool.protocols.base import ProxyServer

logger = logging.getLogger(__name__)


class HttpProxyServer(ProxyServer):
    """HTTP代理服务器实现"""

    async def _create_server(self):
        """创建HTTP代理服务器"""
        return await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
    
    async def _run_server(self):
        """运行HTTP代理服务器"""
        async with self.server:
            await self.server.serve_forever()
    
    async def handle_client(self, reader, writer):
        """处理HTTP代理客户端连接"""
        client_addr = writer.get_extra_info('peername')
        logger.debug(f"新的HTTP代理客户端连接: {client_addr}")
        
        try:
            # 读取HTTP请求头
            headers = await self._read_http_headers(reader)
            if not headers:
                logger.warning("无效的HTTP请求")
                return
            
            # 解析请求行
            request_line = headers[0]
            method, url, version = self._parse_request_line(request_line)
            
            if not method or not url:
                logger.warning(f"无法解析HTTP请求行: {request_line}")
                return
            
            # 处理CONNECT方法（HTTPS隧道）
            if method.upper() == 'CONNECT':
                await self._handle_connect(reader, writer, url, headers)
            else:
                # 处理普通HTTP请求
                await self._handle_http_request(reader, writer, method, url, version, headers)
                
        except (asyncio.IncompleteReadError, ConnectionError) as e:
            logger.debug(f"HTTP连接错误: {str(e)}")
        except Exception as e:
            logger.error(f"处理HTTP客户端时出错: {str(e)}", exc_info=True)
        finally:
            writer.close()
            await writer.wait_closed()
            logger.debug(f"HTTP客户端连接关闭: {client_addr}")
    
    async def _read_http_headers(self, reader):
        """读取HTTP请求头"""
        headers = []
        while True:
            line = await reader.readline()
            if not line or line == b'\r\n':
                break
            headers.append(line.decode('utf-8', errors='ignore').strip())
        return headers
    
    def _parse_request_line(self, request_line):
        """解析HTTP请求行"""
        try:
            parts = request_line.split()
            if len(parts) != 3:
                return None, None, None
            return parts[0], parts[1], parts[2]
        except:
            return None, None, None
    
    async def _handle_connect(self, reader, writer, url, headers):
        """处理HTTPS隧道连接请求"""
        try:
            host, port = url.split(':', 1)
            port = int(port)
            
            # 获取代理节点
            proxy_node = await self.get_proxy()
            if not proxy_node:
                logger.error("没有可用的代理节点")
                writer.write(b'HTTP/1.1 502 Bad Gateway\r\n\r\n')
                await writer.drain()
                return
            
            logger.info(f"使用代理节点 {proxy_node.host}:{proxy_node.port} 连接到 {host}:{port}")
            
            # 尝试通过代理连接到目标服务器
            try:
                proxy_reader, proxy_writer = await asyncio.open_connection(
                    proxy_node.host, proxy_node.port
                )
                
                # 发送连接成功响应
                writer.write(b'HTTP/1.1 200 Connection Established\r\n\r\n')
                await writer.drain()
                
                # 双向转发数据
                await asyncio.gather(
                    self._transfer_data(reader, proxy_writer),
                    self._transfer_data(proxy_reader, writer)
                )
            except Exception as e:
                logger.error(f"连接目标服务器失败: {str(e)}")
                writer.write(b'HTTP/1.1 502 Bad Gateway\r\n\r\n')
                await writer.drain()
                
        except Exception as e:
            logger.error(f"处理CONNECT请求失败: {str(e)}")
            writer.write(b'HTTP/1.1 400 Bad Request\r\n\r\n')
            await writer.drain()
    
    async def _handle_http_request(self, reader, writer, method, url, version, headers):
        """处理普通HTTP请求"""
        try:
            # 解析URL
            parsed_url = urlparse(url)
            host = parsed_url.netloc
            if not host:
                # 从 Host 头中获取
                for header in headers[1:]:
                    if header.lower().startswith('host:'):
                        host = header[5:].strip()
                        break
            
            if not host:
                logger.warning(f"无法确定目标主机: {url}")
                writer.write(b'HTTP/1.1 400 Bad Request\r\n\r\n')
                await writer.drain()
                return
            
            # 分离主机名和端口
            if ':' in host:
                host, port = host.split(':', 1)
                port = int(port)
            else:
                port = 80
            
            # 获取代理节点
            proxy_node = await self.get_proxy()
            if not proxy_node:
                logger.error("没有可用的代理节点")
                writer.write(b'HTTP/1.1 502 Bad Gateway\r\n\r\n')
                await writer.drain()
                return
            
            logger.info(f"使用代理节点 {proxy_node.host}:{proxy_node.port} 连接到 {host}:{port}")
            
            # 重构请求
            path = parsed_url.path
            if not path:
                path = '/'
            if parsed_url.query:
                path += f'?{parsed_url.query}'
            
            # 构建新的请求头
            request_headers = [f"{method} {path} {version}"]
            for header in headers[1:]:
                # 跳过Connection相关头
                if not header.lower().startswith(('proxy-', 'connection:')):
                    request_headers.append(header)
            
            # 添加必要的头部
            request_headers.append('Connection: close')
            
            # 尝试通过代理连接到目标服务器
            try:
                proxy_reader, proxy_writer = await asyncio.open_connection(
                    proxy_node.host, proxy_node.port
                )
                
                # 发送请求到目标服务器
                request = '\r\n'.join(request_headers) + '\r\n\r\n'
                proxy_writer.write(request.encode('utf-8'))
                await proxy_writer.drain()
                
                # 如果有请求体，转发请求体
                content_length = 0
                for header in headers:
                    match = re.match(r'content-length:\s*(\d+)', header.lower())
                    if match:
                        content_length = int(match.group(1))
                        break
                
                if content_length > 0:
                    body = await reader.read(content_length)
                    proxy_writer.write(body)
                    await proxy_writer.drain()
                
                # 读取并转发响应
                response = await proxy_reader.read(8192)
                while response:
                    writer.write(response)
                    await writer.drain()
                    response = await proxy_reader.read(8192)
                
                # 关闭代理连接
                proxy_writer.close()
                await proxy_writer.wait_closed()
                
            except Exception as e:
                logger.error(f"通过代理请求目标服务器失败: {str(e)}")
                writer.write(b'HTTP/1.1 502 Bad Gateway\r\n\r\n')
                await writer.drain()
                
        except Exception as e:
            logger.error(f"处理HTTP请求失败: {str(e)}")
            writer.write(b'HTTP/1.1 400 Bad Request\r\n\r\n')
            await writer.drain()
    
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

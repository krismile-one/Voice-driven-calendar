"""
自签名证书生成工具

纯 Python 实现，无需 openssl。用于开发环境 / 内网部署时快速启用 HTTPS，
使浏览器允许麦克风访问（getUserMedia 需要安全上下文）。

用法：
    from voice_calendar_agent.utils.ssl_helper import generate_self_signed_cert
    cert_path, key_path = generate_self_signed_cert()

    # 或者命令行：
    python -m voice_calendar_agent.utils.ssl_helper
"""

import os
import tempfile
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# 证书存放目录（项目根目录下的 data/ssl/）
_CERT_DIR = None


def _get_cert_dir():
    """获取证书存放目录，自动创建"""
    global _CERT_DIR
    if _CERT_DIR is not None:
        return _CERT_DIR

    # 优先放在项目根目录的 data/ssl/ 下
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    cert_dir = os.path.join(project_root, "data", "ssl")
    os.makedirs(cert_dir, exist_ok=True)
    _CERT_DIR = cert_dir
    return cert_dir


def generate_self_signed_cert(cert_dir=None, common_name="Voice Calendar Agent"):
    """
    使用纯 Python 生成自签名证书（RSA 2048 + SHA256）

    输入：
        cert_dir:      证书存放目录，默认为项目根目录 data/ssl/
        common_name:   证书 CN（通用名称），用于浏览器识别
    输出：
        (cert_path, key_path): 证书文件路径和私钥文件路径
    """
    if cert_dir is None:
        cert_dir = _get_cert_dir()

    cert_path = os.path.join(cert_dir, "selfsigned.crt")
    key_path = os.path.join(cert_dir, "selfsigned.key")

    # 如果证书已存在且未过期，直接复用
    if os.path.exists(cert_path) and os.path.exists(key_path):
        logger.info(f"发现已有自签名证书: {cert_path}")
        return cert_path, key_path

    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
    except ImportError:
        # fallback：使用 subprocess 调用 openssl
        return _generate_with_openssl(cert_dir, common_name)

    logger.info("正在生成自签名证书（cryptography）...")

    # 生成 RSA 私钥
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # 构建证书主题和 SAN
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Voice Calendar Agent"),
    ])

    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
            ]),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )

    # 写入私钥
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    # 写入证书
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    logger.info(f"自签名证书已生成 → {cert_path}")
    logger.info(f"私钥           → {key_path}")
    logger.info("有效期: 365 天")
    return cert_path, key_path


def _generate_with_openssl(cert_dir, common_name):
    """fallback: 使用系统 openssl 生成自签名证书"""
    import subprocess
    import shutil

    openssl = shutil.which("openssl")
    if not openssl:
        raise RuntimeError(
            "未找到 openssl，无法生成证书。\n"
            "请安装 openssl 或安装 Python cryptography 包:\n"
            "  uv add cryptography\n"
            "或手动生成证书后通过 --ssl-certfile / --ssl-keyfile 指定"
        )

    cert_path = os.path.join(cert_dir, "selfsigned.crt")
    key_path = os.path.join(cert_dir, "selfsigned.key")

    logger.info("正在生成自签名证书（openssl）...")
    subprocess.run([
        openssl, "req", "-x509", "-newkey", "rsa:2048",
        "-keyout", key_path, "-out", cert_path,
        "-days", "365", "-nodes",
        "-subj", f"/CN={common_name}",
        "-addext", "subjectAltName=DNS:localhost,DNS:127.0.0.1",
    ], check=True, capture_output=True, text=True)

    logger.info(f"自签名证书已生成 → {cert_path}")
    return cert_path, key_path


# ══════════════════════════════════════════════════════
# CLI: python -m voice_calendar_agent.utils.ssl_helper
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        cert, key = generate_self_signed_cert()
        print(f"\n✅ 证书已就绪")
        print(f"   证书: {cert}")
        print(f"   密钥: {key}")
        print(f"\n启动命令:")
        print(f"   uv run python main.py --api --ssl-certfile \"{cert}\" --ssl-keyfile \"{key}\"")
        print(f"\n   或使用快捷方式:")
        print(f"   uv run python main.py --api --ssl")
    except Exception as e:
        print(f"❌ 生成失败: {e}")

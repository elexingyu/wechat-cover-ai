import streamlit as st
import streamlit_authenticator as stauth
import yaml
from pathlib import Path
import bcrypt

class AuthManager:
    def __init__(self, config_path: str = "auth_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.authenticator = stauth.Authenticate(
            self.config['credentials'],
            self.config['cookie']['name'],
            self.config['cookie']['key'],
            self.config['cookie']['expiry_days']
        )
        self._init_session_state()

    def _load_config(self):
        """加载认证配置"""
        with open(self.config_path) as file:
            return yaml.safe_load(file)
    
    def _save_config(self):
        """保存配置到文件"""
        with open(self.config_path, 'w') as file:
            yaml.dump(self.config, file)

    def _init_session_state(self):
        """初始化session状态"""
        if 'authentication_status' not in st.session_state:
            st.session_state['authentication_status'] = None
        if 'name' not in st.session_state:
            st.session_state['name'] = None
        if 'username' not in st.session_state:
            st.session_state['username'] = None

    def register(self):
        """处理注册逻辑"""
        try:
            if self.is_authenticated:
                return False, "已登录状态下无法注册"
                
            with st.form("registration_form"):
                st.subheader("新用户注册")
                username = st.text_input("用户名", key="registration_username")
                name = st.text_input("姓名", key="registration_name")
                email = st.text_input("邮箱", key="registration_email")
                password = st.text_input("密码", type="password", key="registration_password")
                password2 = st.text_input("确认密码", type="password", key="registration_password2")
                submit = st.form_submit_button("注册")

            if submit:
                # 验证输入
                if not all([username, name, email, password, password2]):
                    return False, "所有字段都必须填写"
                
                if password != password2:
                    return False, "两次输入的密码不一致"
                
                # 检查用户名是否已存在
                if username in self.config['credentials']['usernames']:
                    return False, "用户名已存在"
                
                # 创建新用户
                hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                self.config['credentials']['usernames'][username] = {
                    'email': email,
                    'name': name,
                    'password': hashed_password
                }
                
                # 保存配置
                self._save_config()
                
                # 重新初始化认证器
                self.authenticator = stauth.Authenticate(
                    self.config['credentials'],
                    self.config['cookie']['name'],
                    self.config['cookie']['key'],
                    self.config['cookie']['expiry_days']
                )
                
                return True, "注册成功！请登录"
                
            return None, None
            
        except Exception as e:
            return False, f"注册错误: {str(e)}"

    def login(self):
        """处理登录逻辑"""
        try:
            self.authenticator.login(
                location="main",
                fields={
                    'Form name': '登录',
                    'Username': '用户名',
                    'Password': '密码',
                    'Login': '登录'
                }
            )
            
            return (
                st.session_state['name'],
                st.session_state['authentication_status'],
                st.session_state['username']
            )
        except Exception as e:
            st.error(f"认证错误: {str(e)}")
            return None, None, None

    def logout(self):
        """处理登出逻辑"""
        self.authenticator.logout("退出登录", "sidebar")

    @property
    def is_authenticated(self):
        """检查是否已认证"""
        return st.session_state.get('authentication_status', False)

    def show_login_message(self):
        """显示登录相关的消息"""
        if st.session_state['authentication_status'] == False:
            st.error('用户名或密码错误')
        elif st.session_state['authentication_status'] == None:
            st.warning('请登录后使用') 

    def get_current_user(self):
        """获取当前登录用户的信息"""
        if not self.is_authenticated:
            return None
            
        username = st.session_state['username']
        user_info = self.config['credentials']['usernames'].get(username, {})
        
        return {
            'username': username,
            'name': user_info.get('name'),
            'email': user_info.get('email'),
            'is_admin': username in self.config.get('admin_users', [])
        }

    def show_user_info(self):
        """在侧边栏显示用户信息"""
        if self.is_authenticated:
            user_info = self.get_current_user()
            with st.sidebar:
                st.write("---")
                st.write("👤 用户信息")
                st.write(f"用户名: {user_info['username']}")
                st.write(f"姓名: {user_info['name']}")
                st.write(f"邮箱: {user_info['email']}")
                if user_info['is_admin']:
                    st.write("身份: 管理员") 
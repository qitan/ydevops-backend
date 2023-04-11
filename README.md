## 环境依赖

- Python 3.9
- MySQL 8.0.25

## Jenkins

### plugins:

- http request
- docker
- Docker Pipeline

## 开发环境

部署 MySQL

```shell script
docker run -it --name mysqldb -p 43306:3306 -e MYSQL_ROOT_PASSWORD=password -e MYSQL_DATABASE=ydevopsdb -e MYSQL_USER=devops -e MYSQL_PASSWORD=ops123456 -d mysql:8.0.18 --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci

## 连接报错解决： django.db.utils.OperationalError: (2061, 'RSA Encryption not supported - caching_sha2_password plugin was built with GnuTLS support')
# alter user devops@'%' identified with mysql_native_password by 'ops123456';
```

部署 redis

```shell script
docker run -d --name redis -p 6379:6379 daocloud.io/redis --requirepass 'ops123456'
```

## 依赖安装

mysqlclient:

- debian 系

```shell script
sudo apt install mysql-client-8.0 libmysqlclient-dev python3-dev python-dev libldap2-dev libsasl2-dev libssl-dev
```

- redhat 系

```shell script
--
```

openldap:

- debian 系

```shell script
sudo apt-get install libsasl2-dev python-dev libldap2-dev libssl-dev
```

- redhat 系:

```shell script
yum install python-devel openldap-devel
```

## RBAC

### 获取权限

```python
from rest_framework.schemas.openapi import SchemaGenerator
generator = SchemaGenerator(title='DevOps API')
data = []
try:
    generator.get_schema()
except BaseException as e:
    print(str(e))
finally:
    data = generator.endpoints
    # print(data[0][2].cls.perms_map)
    # print(data[0][2].initkwargs.get('perms_map'))
```

### 初始化配置

```
# migrate 同步表结构
python manage.py makemigrations
python manage.py migrate
```

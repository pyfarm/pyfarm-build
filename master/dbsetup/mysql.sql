DROP DATABASE IF EXISTS pyfarm_unittest_win_26;
DROP DATABASE IF EXISTS pyfarm_unittest_win_27;
DROP DATABASE IF EXISTS pyfarm_unittest_win_32;
DROP DATABASE IF EXISTS pyfarm_unittest_win_34;
DROP DATABASE IF EXISTS pyfarm_unittest_win_33;
DROP DATABASE IF EXISTS pyfarm_unittest_mac_26;
DROP DATABASE IF EXISTS pyfarm_unittest_mac_27;
DROP DATABASE IF EXISTS pyfarm_unittest_mac_32;
DROP DATABASE IF EXISTS pyfarm_unittest_mac_34;
DROP DATABASE IF EXISTS pyfarm_unittest_mac_33;
DROP DATABASE IF EXISTS pyfarm_unittest_linux_26;
DROP DATABASE IF EXISTS pyfarm_unittest_linux_27;
DROP DATABASE IF EXISTS pyfarm_unittest_linux_32;
DROP DATABASE IF EXISTS pyfarm_unittest_linux_34;
DROP DATABASE IF EXISTS pyfarm_unittest_linux_33;
GRANT USAGE ON *.* TO 'buildbot'@'%';
DROP USER 'buildbot'@'%';
CREATE USER 'buildbot'@'%' IDENTIFIED BY '42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2';
CREATE DATABASE pyfarm_unittest_win_26;
CREATE DATABASE pyfarm_unittest_win_27;
CREATE DATABASE pyfarm_unittest_win_32;
CREATE DATABASE pyfarm_unittest_win_34;
CREATE DATABASE pyfarm_unittest_win_33;
CREATE DATABASE pyfarm_unittest_mac_26;
CREATE DATABASE pyfarm_unittest_mac_27;
CREATE DATABASE pyfarm_unittest_mac_32;
CREATE DATABASE pyfarm_unittest_mac_34;
CREATE DATABASE pyfarm_unittest_mac_33;
CREATE DATABASE pyfarm_unittest_linux_26;
CREATE DATABASE pyfarm_unittest_linux_27;
CREATE DATABASE pyfarm_unittest_linux_32;
CREATE DATABASE pyfarm_unittest_linux_34;
CREATE DATABASE pyfarm_unittest_linux_33;
GRANT ALL PRIVILEGES ON pyfarm_unittest_win_26.* TO 'buildbot'@'%' IDENTIFIED BY '42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2';
GRANT ALL PRIVILEGES ON pyfarm_unittest_win_27.* TO 'buildbot'@'%' IDENTIFIED BY '42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2';
GRANT ALL PRIVILEGES ON pyfarm_unittest_win_32.* TO 'buildbot'@'%' IDENTIFIED BY '42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2';
GRANT ALL PRIVILEGES ON pyfarm_unittest_win_34.* TO 'buildbot'@'%' IDENTIFIED BY '42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2';
GRANT ALL PRIVILEGES ON pyfarm_unittest_win_33.* TO 'buildbot'@'%' IDENTIFIED BY '42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2';
GRANT ALL PRIVILEGES ON pyfarm_unittest_mac_26.* TO 'buildbot'@'%' IDENTIFIED BY '42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2';
GRANT ALL PRIVILEGES ON pyfarm_unittest_mac_27.* TO 'buildbot'@'%' IDENTIFIED BY '42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2';
GRANT ALL PRIVILEGES ON pyfarm_unittest_mac_32.* TO 'buildbot'@'%' IDENTIFIED BY '42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2';
GRANT ALL PRIVILEGES ON pyfarm_unittest_mac_34.* TO 'buildbot'@'%' IDENTIFIED BY '42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2';
GRANT ALL PRIVILEGES ON pyfarm_unittest_mac_33.* TO 'buildbot'@'%' IDENTIFIED BY '42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2';
GRANT ALL PRIVILEGES ON pyfarm_unittest_linux_26.* TO 'buildbot'@'%' IDENTIFIED BY '42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2';
GRANT ALL PRIVILEGES ON pyfarm_unittest_linux_27.* TO 'buildbot'@'%' IDENTIFIED BY '42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2';
GRANT ALL PRIVILEGES ON pyfarm_unittest_linux_32.* TO 'buildbot'@'%' IDENTIFIED BY '42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2';
GRANT ALL PRIVILEGES ON pyfarm_unittest_linux_34.* TO 'buildbot'@'%' IDENTIFIED BY '42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2';
GRANT ALL PRIVILEGES ON pyfarm_unittest_linux_33.* TO 'buildbot'@'%' IDENTIFIED BY '42e203517fe6eafda2bfa96580c4973f9cc265b50afebef2';

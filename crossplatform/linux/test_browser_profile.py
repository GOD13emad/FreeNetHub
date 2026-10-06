#!/usr/bin/env python3
import importlib.util,pathlib
p=pathlib.Path(__file__).with_name("freenet_hub_linux.py")
s=importlib.util.spec_from_file_location("fnh",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
root=m.firefox_profile_root()
if pathlib.Path("/snap/firefox/current").exists() and (pathlib.Path.home()/"snap/firefox/common").is_dir():
    assert root == pathlib.Path.home()/"snap/firefox/common/FreeNetHub"
else:
    assert root == m.STATE
prof=m.firefox_profile(False)
text=(prof/"user.js").read_text()
assert 'network.proxy.type", 0' in text
node_prof=m.firefox_profile(proxy_port=m.NODE_SOCKS_PORT)
node_text=(node_prof/"user.js").read_text()
assert 'network.proxy.type", 1' in node_text
assert f'network.proxy.socks_port", {m.NODE_SOCKS_PORT}' in node_text
assert m.browser_proxy_port({"mode":"TOR","detail":{}})==m.SOCKS_PORT
assert m.browser_proxy_port({"mode":"NODE","detail":{}})==m.NODE_SOCKS_PORT
assert m.browser_proxy_port({"mode":"NODE","detail":{"proxyPort":23456}})==23456
assert m.browser_proxy_port({"mode":"DIRECT","detail":{}}) is None
assert m.process_live(99999999) is False
print("LINUX_BROWSER_PROFILE_TEST=PASS")

Summary: Wordpress Theme for Fedora
URL: http://mu.wordpress.org/latest.tar.gz
Name: wordpress-theme-fedora
Version: 1.0.2
Release: 1%{?dist}
Group: Applications/Publishing
License: GPLv2
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Requires: php >= 4.1.0, httpd, php-mysql, wordpress
BuildArch: noarch

%description
This is a theme developed for the Fedora Project for
blogs.fedoraproject.org

%prep
%setup -q -n wordpress-theme-fedora

%build

%install
rm -rf %{buildroot}

mkdir -p %{buildroot}%{_datadir}/wordpress-mu/wp-content/themes/fedora

cp -pr * %{buildroot}%{_datadir}/wordpress-mu/wp-content/themes/fedora

# Remove empty files to make rpmlint happy
find %{buildroot} -empty -exec rm -f {} \;

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%dir %{_datadir}/wordpress-mu/wp-content/themes/fedora
%{_datadir}/wordpress-mu/wp-content/themes/fedora/comments.php
%{_datadir}/wordpress-mu/wp-content/themes/fedora/comments-popup.php
%{_datadir}/wordpress-mu/wp-content/themes/fedora/foo.css
%{_datadir}/wordpress-mu/wp-content/themes/fedora/footer.php
%{_datadir}/wordpress-mu/wp-content/themes/fedora/functions.php
%{_datadir}/wordpress-mu/wp-content/themes/fedora/header.php
%{_datadir}/wordpress-mu/wp-content/themes/fedora/index.php
%{_datadir}/wordpress-mu/wp-content/themes/fedora/rtl.css
%{_datadir}/wordpress-mu/wp-content/themes/fedora/screenshot.png
%{_datadir}/wordpress-mu/wp-content/themes/fedora/sidebar.php
%{_datadir}/wordpress-mu/wp-content/themes/fedora/style.css
%{_datadir}/wordpress-mu/wp-content/themes/fedora/wp-admin_images_logo-ghost.png
%{_datadir}/wordpress-mu/wp-content/themes/fedora/wp-admin_images_logo.gif
%{_datadir}/wordpress-mu/wp-content/themes/fedora/wp-admin_images_wordpress-logo.png
%{_datadir}/wordpress-mu/wp-content/themes/fedora/wp-includes_images_wlw_wp-icon.png

%changelog
* Wed Jun 24 2009 Nick Bebout <nb@fedoraproject.org> - 1.0-1
- initial version of wordpress-mu-theme-fedora

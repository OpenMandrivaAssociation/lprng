Summary: LPRng Print Spooler
Name: LPRng
Version: 3.8.28
Release: %mkrel 7
License: GPL and Artistic
Group: System/Configuration/Printing
Source0: http://www.lprng.com/DISTRIB/LPRng/%{name}-%{version}.tar.bz2
Source1: lprng.startup.bz2
Patch0: LPRng-3.8.27-gcc4.diff
URL: http://www.lprng.com
Buildroot: %{_tmppath}/%{name}-buildroot
# "Conflicts: lpr" is mis-understood, not only the package "lpr" is
# considered as conflicting but also /usr/bin/lpr of another spooler, as
# CUPS.
#Conflicts: lpr
Requires: net-tools
Requires: %{name}-client >= %{version}
Provides: lpr lpddaemon
Requires(post): /sbin/chkconfig, /etc/rc.d/init.d, mktemp, coreutils, gawk
Requires(postun): /sbin/chkconfig, /etc/rc.d/init.d, mktemp, coreutils, gawk
Requires(post): update-alternatives
Requires(preun): update-alternatives
BuildRequires: gdbm-devel gettext-devel

%description
The LPRng software is an enhanced, extended, and portable implementation
of the Berkeley LPR print spooler functionality. While providing the
same interface and meeting RFC1179 requirements, the implementation
is completely new and provides support for the following features:
lightweight (no databases needed) lpr, lpc, and lprm programs; dynamic
redirection of print queues; automatic job holding; highly verbose
diagnostics; multiple printers serving a single queue; client programs
do not need to run SUID root; greatly enhanced security checks; and a
greatly improved permission and authorization mechanism.

The source software compiles and runs on a wide variety of UNIX systems,
and is compatible with other print spoolers and network printers that
use the LPR interface and meet RFC1179 requirements.  LPRng provides
emulation packages for the SVR4 lp and lpstat programs, eliminating the
need for another print spooler package. These emulation packages can be
modified according to local requirements, in order to support vintage
printing systems.

For users that require secure and/or authenticated printing support,
LPRng supports Kerberos V, MIT Kerberos IV Print Support, and PGP
authentication.  LPRng is being adopted by MIT for use as their Campus
Wide printing support system. Additional authentication support is
extremely simple to add.

%package client
Group: System/Configuration/Printing
Summary: LPRng printing client
Requires(post): mktemp, fileutils, textutils, gawk
Requires(postun): mktemp, fileutils, textutils, gawk
Requires(post): update-alternatives
Requires(preun): update-alternatives
Conflicts: LPRng <= 3.8.28-1mdk

%description client
The LPRng software is an enhanced, extended, and portable implementation
of the Berkeley LPR print spooler functionality. While providing the
same interface and meeting RFC1179 requirements, the implementation
is completely new and provides support for the following features:
lightweight (no databases needed) lpr, lpc, and lprm programs; dynamic
redirection of print queues; automatic job holding; highly verbose
diagnostics; multiple printers serving a single queue; client programs
do not need to run SUID root; greatly enhanced security checks; and a
greatly improved permission and authorization mechanism.

This package contains the LPRng client tools.

%prep
%setup -q

# Security fix: Restrict remote access
perl -p -i -e "s/^\#REJECT SERVICE=X/REJECT SERVICE=X NOT SERVER\n\#REJECT SERVICE=X/" lpd.perms.in

%patch0 -p1 -b .gcc4

# Modified startup file with various system checks
bzcat %{SOURCE1} > lprng.startup

%build
CFLAGS="-g" ; export CFLAGS
%configure --enable-nls \
	--with-userid=lp \
	--with-groupid=lp \
#%{!?nokerberos:--enable-kerberos}

perl -p -i -e 's/-DGETENV=\\\"1\\\"/-DGETENV=\\\"0\\\"/g' src/Makefile
make MAKEPACKAGE=YES

%install
rm -rf %{buildroot}

# Installation of locales is broken... Work around it! (They will never get
# it correct)
perl -pi -e "s,prefix =.*,prefix = ${RPM_BUILD_ROOT}%{_prefix},g" po/Makefile
perl -pi -e "s,datadir =.*,datadir = ${RPM_BUILD_ROOT}%{_prefix}/share,g" po/Makefile
perl -pi -e "s,localedir =.*,localedir = ${RPM_BUILD_ROOT}%{_prefix}/share/locale,g" po/Makefile
perl -pi -e "s,gettextsrcdir =.*,gettextsrcdir = ${RPM_BUILD_ROOT}%{_prefix}/share/gettext/po,g" po/Makefile

make SUID_ROOT_PERMS=" 04755" DESTDIR=${RPM_BUILD_ROOT} MAKEPACKAGE=YES mandir=%{_mandir} install
%__cp src/monitor ${RPM_BUILD_ROOT}%{_prefix}/sbin/monitor

# Move locale files to right place, every attempt to fix the Makefiles fails
#cp -a ${RPM_BUILD_ROOT}${RPM_BUILD_ROOT}/* ${RPM_BUILD_ROOT}
#rm -rf ${RPM_BUILD_ROOT}/home

# install init script
mkdir -p %{buildroot}%{_sysconfdir}/rc.d/init.d
install -m755 lprng.startup %{buildroot}%{_sysconfdir}/rc.d/init.d/lpd

# prepare the commands conflicting with CUPS for the update-alternatives
# treatment
( cd $RPM_BUILD_ROOT%{_bindir}
  rm -f lp
  ln -s lpr-lpd lp
  rm -f cancel
  ln -s lprm-lpd cancel
  mv lpr lpr-lpd
  mv lpq lpq-lpd
  mv lprm lprm-lpd
  mv lp lp-lpd
  mv cancel cancel-lpd
  mv lpstat lpstat-lpd
)
( cd $RPM_BUILD_ROOT%{_sbindir}
  mv lpc lpc-lpd
)
( cd $RPM_BUILD_ROOT/%{_mandir}/man1
  mv lpr.1 lpr-lpd.1
  mv lpq.1 lpq-lpd.1
  mv lprm.1 lprm-lpd.1
  mv lp.1 lp-lpd.1
  mv cancel.1 cancel-lpd.1
  mv lpstat.1 lpstat-lpd.1
)
( cd $RPM_BUILD_ROOT/%{_mandir}/man8
  mv lpc.8 lpc-lpd.8
)

# Conflict with setup package
rm -f %buildroot%_sysconfdir/printcap

# Suppress automatic replacement of "echo" by "gprintf" in the LPRng
# startup script by RPM. This automatic replacement is broken.
export DONT_GPRINTIFY=1

%clean
rm -rf %{buildroot}

%post
/sbin/chkconfig --add lpd
%{_sbindir}/update-alternatives --install %{_sbindir}/lpc lpc %{_sbindir}/lpc-lpd 5 --slave %{_mandir}/man8/lpc.8.bz2 lpc.1.bz2 %{_mandir}/man8/lpc-lpd.8.bz2

%post client
if [ -w /etc/printcap ] ; then
  TMP1=`mktemp /etc/printcap.XXXXXX`
  gawk '
    BEGIN { first = 1; cont = 0; last = "" }
    /^[:space:]*#/      { if(cont) sub("\\\\$", "", last)}
    { if(first == 0) print last }
    { first = 0 }
    { last = $0 }
    { cont = 0 }
    /\\$/ { cont = 1 }
    END {sub("\\\\$", "", last); print last}
  ' /etc/printcap > ${TMP1} && cat ${TMP1} > /etc/printcap && rm -f ${TMP1}
fi

# Set up update-alternatives entries
%{_sbindir}/update-alternatives --install %{_bindir}/lpr lpr %{_bindir}/lpr-lpd 5 --slave %{_mandir}/man1/lpr.1.bz2 lpr.1.bz2 %{_mandir}/man1/lpr-lpd.1.bz2
%{_sbindir}/update-alternatives --install %{_bindir}/lpq lpq %{_bindir}/lpq-lpd 5 --slave %{_mandir}/man1/lpq.1.bz2 lpq.1.bz2 %{_mandir}/man1/lpq-lpd.1.bz2
%{_sbindir}/update-alternatives --install %{_bindir}/lprm lprm %{_bindir}/lprm-lpd 5 --slave %{_mandir}/man1/lprm.1.bz2 lprm.1.bz2 %{_mandir}/man1/lprm-lpd.1.bz2
%{_sbindir}/update-alternatives --install %{_bindir}/lp lp %{_bindir}/lp-lpd 5 --slave %{_mandir}/man1/lp.1.bz2 lp.1.bz2 %{_mandir}/man1/lp-lpd.1.bz2
%{_sbindir}/update-alternatives --install %{_bindir}/cancel cancel %{_bindir}/cancel-lpd 5 --slave %{_mandir}/man1/cancel.1.bz2 cancel.1.bz2 %{_mandir}/man1/cancel-lpd.1.bz2
%{_sbindir}/update-alternatives --install %{_bindir}/lpstat lpstat %{_bindir}/lpstat-lpd 5 --slave %{_mandir}/man1/lpstat.1.bz2 lpstat.1.bz2 %{_mandir}/man1/lpstat-lpd.1.bz2

%preun
if [ "$1" = 0 ]; then
  %{_sysconfdir}/rc.d/init.d/lpd stop >/dev/null 2>&1
  /sbin/chkconfig --del lpd
  %{_sbindir}/update-alternatives --remove lpc /usr/sbin/lpc-lpd
fi

%preun client

if [ "$1" = 0 ]; then
  # Remove update-alternatives entries
  %{_sbindir}/update-alternatives --remove lpr /usr/bin/lpr-lpd
  %{_sbindir}/update-alternatives --remove lpq /usr/bin/lpq-lpd
  %{_sbindir}/update-alternatives --remove lprm /usr/bin/lprm-lpd
  %{_sbindir}/update-alternatives --remove lp /usr/bin/lp-lpd
  %{_sbindir}/update-alternatives --remove cancel /usr/bin/cancel-lpd
  %{_sbindir}/update-alternatives --remove lpstat /usr/bin/lpstat-lpd

fi

%postun
if [ "$1" -ge "1" ]; then
  %{_sysconfdir}/rc.d/init.d/lpd condrestart >/dev/null 2>&1
fi

%files
%defattr(-,root,root)
%attr(755,root,root) %config(noreplace) %{_sysconfdir}/lpd
%attr(644,root,root) %config(noreplace) %{_sysconfdir}/printcap*
%config %{_sysconfdir}/rc.d/init.d/lpd
%_sbindir/checkpc
%_sbindir/lpd
%_sbindir/lprng_certs
%_sbindir/lprng_index_certs
%_sbindir/monitor
%attr(755,lp,lp) %{_sbindir}/lpc-lpd
%attr(755,root,root)  %_libdir/filters/*
%attr(755,root,root)  %_libdir/liblpr*
%{_mandir}/*/*
%{_datadir}/locale/fr/LC_MESSAGES/LPRng.mo
%doc CHANGES CONTRIBUTORS COPYRIGHT INSTALL LICENSE 
%doc README* VERSION Y2KCompliance
%doc DOCS/*.htm* DOCS/*.jpg DOCS/*.png DOCS/*.txt DOCS/*.pdf
%doc DOCS/LPRng-Reference-Multipart

%files client
%defattr(-,root,root)
%attr(755,lp,lp) %{_bindir}/lpq-lpd
%attr(755,lp,lp) %{_bindir}/lprm-lpd
%attr(755,lp,lp) %{_bindir}/lpr-lpd
%attr(755,lp,lp) %{_bindir}/lpstat-lpd
%{_bindir}/lp-lpd
%{_bindir}/cancel-lpd
%attr(755,root,root) %config(noreplace) %{_sysconfdir}/lpd
%doc CHANGES CONTRIBUTORS COPYRIGHT INSTALL LICENSE 
%doc README* VERSION Y2KCompliance
%doc DOCS/*.htm* DOCS/*.jpg DOCS/*.png DOCS/*.txt DOCS/*.pdf
%doc DOCS/LPRng-Reference-Multipart


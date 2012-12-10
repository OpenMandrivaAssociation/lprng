%define rname LPRng

Summary:	LPRng Print Spooler
Name:		lprng
Version:	3.8.32
Release:	%mkrel 6
License:	GPL and Artistic
Group:		System/Configuration/Printing
URL:		http://www.lprng.com
Source0:	http://www.lprng.com/DISTRIB/LPRng/%{rname}-%{version}.tgz
Source1:	lprng.startup
Patch0:		LPRng-3.8.27-gcc4.diff
Patch1:		LPRng-typo_fix.diff
Patch2:		lprng-3.8.32-Werror=format-security.patch
# "Conflicts: lpr" is mis-understood, not only the package "lpr" is
# considered as conflicting but also /usr/bin/lpr of another spooler, as
# CUPS.
#Conflicts: lpr
Requires:	net-tools
Requires:	%{name}-client >= %{version}
Obsoletes:	%{rname}
Provides:	lpr lpddaemon
Requires(post): update-alternatives
Requires(preun): update-alternatives
BuildRequires:	gdbm-devel
BuildRequires:	gettext-devel
BuildRoot:	%{_tmppath}/%{rname}-%{version}-%{release}-buildroot

%description
The LPRng software is an enhanced, extended, and portable implementation of
the Berkeley LPR print spooler functionality. While providing the same
interface and meeting RFC1179 requirements, the implementation is completely
new and provides support for the following features: lightweight (no databases
needed) lpr, lpc, and lprm programs; dynamic redirection of print queues;
automatic job holding; highly verbose diagnostics; multiple printers serving a
single queue; client programs do not need to run SUID root; greatly enhanced
security checks; and a greatly improved permission and authorization mechanism.

%package	client
Group:		System/Configuration/Printing
Summary:	LPRng printing client
Requires(post): update-alternatives
Requires(preun): update-alternatives
Conflicts:	LPRng <= 3.8.28-1mdk
Obsoletes:	%{rname}-client

%description	client
The LPRng software is an enhanced, extended, and portable implementation of
the Berkeley LPR print spooler functionality. While providing the same
interface and meeting RFC1179 requirements, the implementation is completely
new and provides support for the following features: lightweight (no databases
needed) lpr, lpc, and lprm programs; dynamic redirection of print queues;
automatic job holding; highly verbose diagnostics; multiple printers serving a
single queue; client programs do not need to run SUID root; greatly enhanced
security checks; and a greatly improved permission and authorization mechanism.

This package contains the LPRng client tools.

%prep

%setup -q -n %{rname}-%{version}

# Security fix: Restrict remote access
perl -p -i -e "s/^\#REJECT SERVICE=X/REJECT SERVICE=X NOT SERVER\n\#REJECT SERVICE=X/" lpd.perms.in

%patch0 -p1 -b .gcc4
%patch1 -p0
%patch2 -p1

# Modified startup file with various system checks
cp %{SOURCE1} lprng.startup

%build
%serverbuild

%configure2_5x \
    --enable-nls \
    --with-userid=lp \
    --with-groupid=lp \
    --disable-werror
#%{!?nokerberos:--enable-kerberos}

make

%install
rm -rf %{buildroot}

# Suppress automatic replacement of "echo" by "gprintf" in the LPRng
# startup script by RPM. This automatic replacement is broken.
export DONT_GPRINTIFY=1

# Installation of locales is broken... Work around it! (They will never get
# it correct)
perl -pi -e "s,prefix =.*,prefix = %{buildroot}%{_prefix},g" po/Makefile
perl -pi -e "s,datadir =.*,datadir = %{buildroot}%{_prefix}/share,g" po/Makefile
perl -pi -e "s,localedir =.*,localedir = %{buildroot}%{_prefix}/share/locale,g" po/Makefile
perl -pi -e "s,gettextsrcdir =.*,gettextsrcdir = %{buildroot}%{_prefix}/share/gettext/po,g" po/Makefile

make SUID_ROOT_PERMS=" 04755" \
    DESTDIR=%{buildroot} \
    MAKEPACKAGE=YES \
    DATADIR="%{buildroot}%{_datadir}/LPRng" \
    mandir=%{_mandir} install

%__cp src/monitor %{buildroot}%{_prefix}/sbin/monitor

# install init script
install -d %{buildroot}%{_initrddir}
install -m0755 lprng.startup %{buildroot}%{_initrddir}/lpd

# prepare the commands conflicting with CUPS for the update-alternatives
# treatment
( cd %{buildroot}%{_bindir}
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
( cd %{buildroot}%{_sbindir}
  mv lpc lpc-lpd
)
( cd %{buildroot}%{_mandir}/man1
  mv lpr.1 lpr-lpd.1
  mv lpq.1 lpq-lpd.1
  mv lprm.1 lprm-lpd.1
  mv lp.1 lp-lpd.1
  mv cancel.1 cancel-lpd.1
  mv lpstat.1 lpstat-lpd.1
)
( cd %{buildroot}%{_mandir}/man8
  mv lpc.8 lpc-lpd.8
)

# Conflict with setup package
rm -f %{buildroot}%{_sysconfdir}/printcap
rm -rf %{buildroot}%{_datadir}/LPRng
rm -f %{buildroot}%{_sysconfdir}/rc.d/init.d/lpd.sample

%find_lang %{rname}

%post
/sbin/chkconfig --add lpd
%{_sbindir}/update-alternatives --install %{_sbindir}/lpc lpc %{_sbindir}/lpc-lpd 5 --slave \
    %{_mandir}/man8/lpc.8%{_extension} lpc.8%{_extension} %{_mandir}/man8/lpc-lpd.8%{_extension}

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
%{_sbindir}/update-alternatives --install %{_bindir}/lpr lpr %{_bindir}/lpr-lpd 5 \
    --slave %{_mandir}/man1/lpr.1%{_extension} lpr.1%{_extension} %{_mandir}/man1/lpr-lpd.1%{_extension}

%{_sbindir}/update-alternatives --install %{_bindir}/lpq lpq %{_bindir}/lpq-lpd 5 \
    --slave %{_mandir}/man1/lpq.1%{_extension} lpq.1%{_extension} %{_mandir}/man1/lpq-lpd.1%{_extension}

%{_sbindir}/update-alternatives --install %{_bindir}/lprm lprm %{_bindir}/lprm-lpd 5 \
    --slave %{_mandir}/man1/lprm.1%{_extension} lprm.1%{_extension} %{_mandir}/man1/lprm-lpd.1%{_extension}

%{_sbindir}/update-alternatives --install %{_bindir}/lp lp %{_bindir}/lp-lpd 5 \
    --slave %{_mandir}/man1/lp.1%{_extension} lp.1%{_extension} %{_mandir}/man1/lp-lpd.1%{_extension}

%{_sbindir}/update-alternatives --install %{_bindir}/cancel cancel %{_bindir}/cancel-lpd 5 \
    --slave %{_mandir}/man1/cancel.1%{_extension} cancel.1%{_extension} %{_mandir}/man1/cancel-lpd.1%{_extension}

%{_sbindir}/update-alternatives --install %{_bindir}/lpstat lpstat %{_bindir}/lpstat-lpd 5 \
    --slave %{_mandir}/man1/lpstat.1%{_extension} lpstat.1%{_extension} %{_mandir}/man1/lpstat-lpd.1%{_extension}

%preun
if [ "$1" = 0 ]; then
    %{_initrddir}/lpd stop >/dev/null 2>&1
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
    %{_initrddir}/lpd condrestart >/dev/null 2>&1
fi

%clean
rm -rf %{buildroot}

%files -f %{rname}.lang
%defattr(-,root,root)
%doc CHANGES CONTRIBUTORS COPYRIGHT INSTALL LICENSE 
%doc README* VERSION Y2KCompliance
%doc DOCS/*.htm* DOCS/*.jpg DOCS/*.png DOCS/*.txt DOCS/*.pdf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/printcap*
%attr(0755,root,root) %{_initrddir}/lpd
%{_sbindir}/checkpc
%{_sbindir}/lpd
%{_sbindir}/lprng_certs
%{_sbindir}/lprng_index_certs
%{_sbindir}/monitor
%attr(0755,lp,lp) %{_sbindir}/lpc-lpd
%attr(0755,root,root) %{_libdir}/filters/*
%attr(0755,root,root) %{_libdir}/liblpr*
%{_mandir}/*/*

%files client
%defattr(-,root,root)
%doc CHANGES CONTRIBUTORS COPYRIGHT INSTALL LICENSE 
%doc README* VERSION Y2KCompliance
%doc DOCS/*.htm* DOCS/*.jpg DOCS/*.png DOCS/*.txt DOCS/*.pdf
%attr(0755,root,root) %dir %{_sysconfdir}/lpd
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/lpd/*
%attr(0755,lp,lp) %{_bindir}/lpq-lpd
%attr(0755,lp,lp) %{_bindir}/lprm-lpd
%attr(0755,lp,lp) %{_bindir}/lpr-lpd
%attr(0755,lp,lp) %{_bindir}/lpstat-lpd
%{_bindir}/lp-lpd
%{_bindir}/cancel-lpd


%changelog
* Fri Dec 10 2010 Oden Eriksson <oeriksson@mandriva.com> 3.8.32-6mdv2011.0
+ Revision: 620261
- the mass rebuild of 2010.0 packages

* Mon Sep 14 2009 Thierry Vignaud <tv@mandriva.org> 3.8.32-5mdv2010.0
+ Revision: 439611
- rebuild

* Wed Mar 25 2009 Gustavo De Nardin <gustavodn@mandriva.com> 3.8.32-4mdv2009.1
+ Revision: 360991
- fixed config dir permissions and package ownerships (bug 49051)

* Tue Mar 24 2009 Gustavo De Nardin <gustavodn@mandriva.com> 3.8.32-3mdv2009.1
+ Revision: 360795
- fixed alternatives names (bug 49071)

* Tue Jan 27 2009 Gustavo De Nardin <gustavodn@mandriva.com> 3.8.32-2mdv2009.1
+ Revision: 334602
- fixed GCC format string complaints
- new release with initscript fixes
- cleanup unneeded code in the initscript, which tried to setup the network
  before bringing up lprng (...); this is ensured by LSB $network facility
- cleanup dead, commented out, code in the initscript, which tried to setup
  the network before bringing up lprng (...) this is ensured by LSB $network
  facility
- made initscript use #!/bin/bash, for it uses bashisms
- fixed init script to have LSB headers, based on patch for bug #47300 by Sylvie Terjan

* Sat Jul 26 2008 Oden Eriksson <oeriksson@mandriva.com> 3.8.32-1mdv2009.0
+ Revision: 250300
- 3.8.32
- lowerecase'd due to case haters
- fix build, and other spec file stuff...
- for the case haters

  + Thierry Vignaud <tv@mandriva.org>
    - rebuild
    - rebuild
    - require coreutils instead of fileutils & textutils


* Tue Jun 20 2006 Lenny Cartier <lenny@mandriva.com> 3.8.28-4mdv2007.0
- rebuild

* Tue May 16 2006 Olivier Thauvin <nanardon@mandriva.org> 3.8.28-3mdk
- add conflicts to ensure upgrade works

* Fri Apr 21 2006 Olivier Thauvin <nanardon@mandriva.org> 3.8.28-2mdk
- %%mkrel
- some clean up
- split package between the server and the client

* Wed Nov 30 2005 Oden Eriksson <oeriksson@mandriva.com> 3.8.28-1mdk
- 3.8.28
- added P0 to make it compile with gcc4 (debian)

* Mon Aug 23 2004 Olivier Thauvin <thauvin@aerov.jussieu.fr> 3.8.27-1mdk
- 3.8.27
- remove printcap, conflict with setup

* Thu Mar 18 2004 Olivier Thauvin <thauvin@aerov.jussieu.fr> 3.8.26-2mdk
- Fix permission on %%_sysconfdir/lpd
- clean list files

* Fri Mar 05 2004 Till Kamppeter <till@mandrakesoft.com> 3.8.26-1mdk
- Version 3.8.26 (after a long break LPRng is under development again).


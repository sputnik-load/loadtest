#/bin/bash

# Установка perl-модулей, необходимых для скриптов генерации данных репозитария LoadTest на 26.05.16.

yum install perl-String-Random.noarch
yum install perl-Data-Dump.noarch
yum install perl-Data-UUID.x86_64
yum install perl-List-MoreUtils.x86_64 # Provide the stuff missing in List::Util.
yum install perl-MIME-Base64-URLSafe.noarch
yum install perl-POSIX-strptime.x86_64
yum install perl-Time-Piece.x86_64
yum install perl-Time-Clock.noarch
yum install perl-Unicode-String.x86_64
yum install perl-URI-Encode.noarch
yum install perl-URI-Escape-XS.x86_64 # Perl module that is a drop-in replacement for URI::Escape.
yum install perl-String-Random.noarch
yum install perl-Data-GUID.noarch
yum install perl-Time-modules.noarch # Perl modules for parsing dates and times; includes Time::Seconds.

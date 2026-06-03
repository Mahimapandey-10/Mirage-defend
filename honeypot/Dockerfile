FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    openssh-server curl wget git vim net-tools python3 mysql-client \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m -s /bin/bash ubuntu && \
    echo "ubuntu:helloworld" | chpasswd && \
    mkdir -p /home/ubuntu/.ssh && \
    mkdir -p /var/run/sshd
RUN echo "Port 22" > /etc/ssh/sshd_config && \
    echo "PermitRootLogin yes" >> /etc/ssh/sshd_config && \
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config && \
    echo "KbdInteractiveAuthentication no" >> /etc/ssh/sshd_config && \
    echo "UsePAM yes" >> /etc/ssh/sshd_config && \
    echo "Subsystem sftp /usr/lib/openssh/sftp-server" >> /etc/ssh/sshd_config
RUN mkdir -p /var/www/app/config
COPY fake_files/database.yml /var/www/app/config/
COPY fake_files/app_secrets.env /var/www/app/
COPY fake_files/backup.sql /var/www/app/
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]

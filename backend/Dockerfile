# Stage 1: Extract missing so files from Debian packages
FROM debian:bookworm-slim AS so-extract

RUN apt-get update && \
    apt-get install --no-install-recommends -y zlib1g && \
    find / -name "libz.so.1" 2>/dev/null | sort && \
    apt-get install --no-install-recommends -y libgl1 && \
    find / -name "libGL.so.1" 2>/dev/null | sort && \
    apt-get install --no-install-recommends -y libglib2.0-0 && \
    find / -name "libgthread-2.0.so.0" 2>/dev/null | sort && \
    find / -name "libglib-2.0.so.0" 2>/dev/null | sort && \
    apt-get install --no-install-recommends -y libglvnd0 && \
    find / -name "libGLdispatch.so.0" 2>/dev/null | sort && \
    apt-get install --no-install-recommends -y libglx0 && \
    find / -name "libGLX.so.0" 2>/dev/null | sort

# libGLX.so.0

# Stage 2: Build the application
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV and other libraries
RUN apt-get update && apt-get install -y \
    libgl1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY . .

# Expose port 3002
EXPOSE 3002

RUN dpkg -S /usr/lib/x86_64-linux-gnu/libGLX.so.0

# Upgrade setuptools to fix CVE-2024-6345
RUN pip install --upgrade setuptools==70.0.0

# Remove unnecessary system packages
RUN apt-get update && \
    # Remove libaom3 to fix CVE-2023-6879, CVE-2023-39616
    # DEBIAN_FRONTEND=noninteractive apt-get remove --purge -y libaom3 && \
    # # Remove libexpat1 to fix CVE-2023-52425, CVE-2024-8176
    # DEBIAN_FRONTEND=noninteractive apt-get remove --purge -y libexpat1 && \
    # # Remove libharfbuzz0b to fix CVE-2023-25193
    # DEBIAN_FRONTEND=noninteractive apt-get remove --purge -y libharfbuzz0b && \
    # # Remove libjxl0.7 to fix CVE-2023-0645, CVE-2023-35790
    # DEBIAN_FRONTEND=noninteractive apt-get remove --purge -y libjxl0.7 && \
    # # Remove libmbedcrypto7 to fix CVE-2024-23775
    # DEBIAN_FRONTEND=noninteractive apt-get remove --purge -y libmbedcrypto7 && \
    # # Remove libsndfile1 to fix CVE-2022-33064, CVE-2022-33065
    # DEBIAN_FRONTEND=noninteractive apt-get remove --purge -y libsndfile1 && \
    # # Remove libtiff6 to fix CVE-2023-52355
    # DEBIAN_FRONTEND=noninteractive apt-get remove --purge -y libtiff6 && \
    # Remove libxml2 to fix CVE-2024-25062, CVE-2024-56171, CVE-2025-24928, CVE-2025-27113
    DEBIAN_FRONTEND=noninteractive apt-get remove --purge -y libxml2 && \
    # Remove perl to fix CVE-2023-31484
    DEBIAN_FRONTEND=noninteractive apt-get remove --purge --allow-remove-essential -y perl-base && \
    DEBIAN_FRONTEND=noninteractive apt-get remove --purge -y perl-modules-5.36 && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Remove libz1g to fix CVE-2023-45853
# WARNING: This will uninstall the package manager, which will prevent us from removing other packages, so this should be done last
RUN dpkg --purge --force-all zlib1g

# Copy all extracted shared libs
COPY --from=so-extract /usr/lib/x86_64-linux-gnu/libz.so.1 /usr/lib/x86_64-linux-gnu/libz.so.1
COPY --from=so-extract /usr/lib/x86_64-linux-gnu/libGL.so.1 /usr/lib/x86_64-linux-gnu/libGL.so.1
COPY --from=so-extract /usr/lib/x86_64-linux-gnu/libgthread-2.0.so.0 /usr/lib/x86_64-linux-gnu/libgthread-2.0.so.0
COPY --from=so-extract /usr/lib/x86_64-linux-gnu/libglib-2.0.so.0 /usr/lib/x86_64-linux-gnu/libglib-2.0.so.0
COPY --from=so-extract /usr/lib/x86_64-linux-gnu/libGLdispatch.so.0 /usr/lib/x86_64-linux-gnu/libGLdispatch.so.0
COPY --from=so-extract /usr/lib/x86_64-linux-gnu/libGLX.so.0 /usr/lib/x86_64-linux-gnu/libGLX.so.0

CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "3002"]
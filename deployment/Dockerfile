FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# working directory
WORKDIR /app

# Copy only requirements first so we can install dependencies before copying source (better cache)
COPY requirements.txt .


# Install build deps, install Python packages, then remove build deps in the same layer to avoid leaving them
# in the final image. This reduces final image size while still allowing compilation when needed.
RUN apt-get update \
	 && apt-get install -y --no-install-recommends \
		 build-essential \
		 gcc \
		 libpq-dev \
		 libjpeg-dev \
		 zlib1g-dev \
		 libffi-dev \
		 libmagic1 \
	&& pip install --no-cache-dir -r requirements.txt \
	&& apt-get remove -y --purge build-essential gcc \
	&& apt-get autoremove -y \
	&& rm -rf /var/lib/apt/lists/*

# Now copy the rest of the source
COPY . .

EXPOSE 80

# keep setuptools up to date
CMD ["gunicorn", "--bind=0.0.0.0:80", "vedinka.wsgi"]

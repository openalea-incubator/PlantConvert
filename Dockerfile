FROM continuumio/miniconda3

WORKDIR /src/OpenAlea.PlantConvert

COPY environment.yml /src/OpenAlea.PlantConvert/

RUN conda install -c conda-forge gcc python=3.10 \
    && conda env update -n base -f environment.yml

COPY . /src/OpenAlea.PlantConvert

RUN pip install --no-deps -e .

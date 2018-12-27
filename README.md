#Deployment instructions

1. Clone repo:
    ```
    git clone https://github.com/deepmipt/log_analysis.git
    ```
2. `cd` log_analysis dir:
    ```
    cd log_analysis
    ```
3. Create and activate virtual env:
    ```
    virtualenv env -p python3.6
    source env/bin/activate
    ```
4. Install dependencies:
    ```
    pip install -r requirements.txt
    ```
5. Set Jupyter password:
    ```
    jupyter notebook password
    ```
6. Generate Jupyter config:
    ```
    jupyter notebook --generate-config
    ```
7. Run deployment script:
    ```
    python deploy.py 
    ```
8. Run launch script:
    ```
    ./run_log_analysis.sh
    ```
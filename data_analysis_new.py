import os.path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import json
from sklearn.metrics import mean_squared_error, f1_score,confusion_matrix
from statsmodels.tsa.stattools import acf
from abc import ABC, abstractmethod
from copy import deepcopy
from statsmodels.tsa.seasonal import seasonal_decompose
from utlis.plot import TimeSeriesPlot,plot_grouped_time_series
from utlis.preprocessing import TimeSeriesPreprocessor
from AutoMachineLearning import TimeSeriesAutoML,GridSearchTuner
from model.models import LSTMModel,GRUModel,BaseTCNModel
from matplotlib.dates import DateFormatter, MonthLocator
from datetime import datetime, timedelta
import torch
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, TensorDataset
from torch import nn
class BaseConfig:
    def __init__(self, path,task,group_by=None, label=None, excluded_features=None):
        self.group_by = group_by
        self.label = label
        self.excluded_features = excluded_features or []
        self.task = task
        self.dataset_path = path
    def update_excluded_features(self, new_excluded_features):
        self.excluded_features.update(new_excluded_features)
class TimeSeriesConfig(BaseConfig):
    def __init__(self, timestamp_column, resample_rule=None,start=None,start_test=None,end=None,include_label=True, **kwargs):
        super().__init__(**kwargs)
        self.timestamp_column = timestamp_column
        self.resample_rule = resample_rule  # 可选，用于定义重采样规则
        self.start = start
        self.start_test = start_test
        self.end = end
        self.include_label = include_label
class DataAnalysisInterface(ABC):
    def __init__(self,config):
        self.config = config
        self.dataframe = None
        self.processed_dataframe = None

    def load_data(self,path=None):
        if path is None:
            filepath = self.config.dataset_path
        else:
            filepath = path
        self.dataframe = pd.read_csv(filepath) if filepath.endswith('.csv') else pd.read_excel(filepath)
        self.processed_dataframe = deepcopy(self.dataframe)
        print(f'Loading data from {filepath}')

    @abstractmethod
    def preprocess_data(self):
        self.processed_dataframe.dropna(axis=1, how='all', inplace=True)

        if self.config.excluded_features:
            self.processed_dataframe.drop(columns=self.config.excluded_features, inplace=True, errors='ignore')

    @abstractmethod
    def analyze_data(self):
        """Perform data analysis."""
        pass

    def update_config(self, new_excluded_features):
        self.config.update_excluded_features(new_excluded_features)
        print("Config updated with new excluded features:", self.config.excluded_features)
        self.preprocess_data()  # 重新预处理数据
        self.analyze_data()  # 重新分析数据
class TimeSeriesAnalysis(DataAnalysisInterface):
    def preprocess_data(self):
        super().preprocess_data()
        # 设置时间索引
        if self.config.timestamp_column in self.processed_dataframe.columns:
            self.processed_dataframe[self.config.timestamp_column] = pd.to_datetime(
                self.processed_dataframe[self.config.timestamp_column])
            self.processed_dataframe.set_index(self.config.timestamp_column, inplace=True)
            print(f"Timestamp column '{self.config.timestamp_column}' set as index.")

        columns_to_fill = self.processed_dataframe.columns.difference([self.config.label])

        # Apply group and fill logic
        if self.config.group_by and self.config.group_by in self.processed_dataframe.columns:
            # Group by the specified column and apply filling only to the specified columns to fill
            grouped = self.processed_dataframe.groupby(self.config.group_by)
            self.processed_dataframe[columns_to_fill] = grouped[columns_to_fill].apply(
                lambda group: group.ffill().bfill())
            print("Data grouped by", self.config.group_by, "and missing values in features filled.")
        else:
            # Apply filling to the entire dataset excluding the label column
            self.processed_dataframe[columns_to_fill] = self.processed_dataframe[columns_to_fill].ffill().bfill()
            print("Missing values in features filled based on time adjacency without grouping.")

    def get_partial_data(self, start=None, end=None):
        # Slicing directly using the datetime index if start and/or end are provided
        if start and end:
            return self.processed_dataframe.loc[start:end].copy()
        elif start:
            return self.processed_dataframe.loc[start:].copy()
        elif end:
            return self.processed_dataframe.loc[:end].copy()
        else:
            return self.processed_dataframe.copy()

    def analyze_data(self):
        analyzer = TimeSeriesPlot(self.config, self.processed_dataframe)
        analyzer.analyze_data()


if __name__ == '__main__':
    time_series_config = TimeSeriesConfig(
        task = 'warehouse',
        timestamp_column='date',
        label='next_day_storage',
        group_by='warehouse_name',
        start='2023-08-01',
        start_test='2023-11-07',
        end='2023-11-30',
        path='train_data.csv'
    )
    # time_series_config = TimeSeriesConfig(
    #     task = 'nasa',
    #     timestamp_column='time_in_cycles',
    #     label='RUL',
    #     group_by='engine_no',
    #     excluded_features=['op_setting_3','sensor_16','sensor_19'],
    # )
    start_date = time_series_config.start
    start_test_date = time_series_config.start_test
    end_date = time_series_config.end



    analysis = TimeSeriesAnalysis(time_series_config)
    analysis.load_data()
    analysis.preprocess_data()
    print(analysis.processed_dataframe.head())
    # analysis.analyze_data()

    # look back set up, look back = 1 can use auto regression task, e.g. arima
    # look back>1 use rnn based method
    look_back = 3
    # adjust to predict the next n time stamp
    predict_time_stamp = 1


    data = analysis.get_partial_data(end=start_test_date)
    preprocessor = TimeSeriesPreprocessor(time_series_config, look_back=look_back,predict_time_stamp=predict_time_stamp)
    preprocessor.fit(data)
    preprocessed_training_data, preprocessed_training_label = preprocessor.transform(data)

    # should specify the dimension here
    input_dimension, output_dimension = preprocessor.num_features, predict_time_stamp









    auto_ml = TimeSeriesAutoML(time_series_config)

    auto_ml.add_model('LSTM',LSTMModel(input_dimension,output_dimension))
    # auto_ml.add_model('GRU', GRUModel(input_dimension, output_dimension))
    # auto_ml.add_model('TCN',BaseTCNModel(input_dimension,output_dimension))
    auto_ml.add_tuner('GridSearch', GridSearchTuner(num_folds=2))

    auto_ml.run_experiments(preprocessed_training_data, preprocessed_training_label)
    train_result = auto_ml.train_result
    train_predictions = train_result['LSTM']['train_prediction']
    train_predictions = preprocessor.inverse_transform_labels(train_predictions)
    train_predictions = [int(i) for i in train_predictions]
    n_groups = len(preprocessed_training_label)
    n_train_sampels = len(train_predictions)/n_groups

    result = {
        'train':{},
        'test':{}
    }
    start_index_train = 0
    num_groups = len(preprocessed_training_label)
    start_date_datetime = pd.to_datetime(start_date)
    date_range_start = start_date_datetime + pd.DateOffset(days=look_back)

    date_range = pd.date_range(start=date_range_start, end=start_test_date, freq='D')
    date_strings = date_range.format(formatter=lambda x: x.strftime('%Y-%m-%d'))
    result['train']['date_range'] = date_strings
    for i,(name,truth) in enumerate(preprocessed_training_label.items()):
        train_truth = preprocessor.inverse_transform_labels(np.array(truth))
        train_truth = np.squeeze(train_truth)
        train_truth = train_truth.tolist()
        train_truth = [int(i) for i in train_truth]
        num_train = len(train_truth)
        result['train'][name] = {
            'prediction': train_predictions[start_index_train:start_index_train + num_train],
            'truth': train_truth,
            }
        start_index_train += num_train

    test_prediction = {}
    start_date_datetime = pd.to_datetime(start_test_date)
    start_test_date = start_date_datetime+pd.DateOffset(days=1)
    date_range = pd.date_range(start=start_test_date, end=end_date, freq='D')
    date_strings = date_range.format(formatter=lambda x: x.strftime('%Y-%m-%d'))
    result['test'] = {name: {'prediction': [], 'truth': []} for name in preprocessed_training_label.keys()}
    result['test']['date_range'] = date_strings
    # 将 Timestamp 对象转换为字符串以便使用 strptime
    start_test_date_str = start_test_date.strftime('%Y-%m-%d')
    cur_date = datetime.strptime(start_test_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')


    while cur_date<end_date:
        # read and process again, since new data is coming
        analysis.load_data()
        analysis.preprocess_data()

        cur_start_test_date = cur_date + timedelta(days=1) - timedelta(days=look_back)
        cur_start_test_date = cur_start_test_date.strftime('%Y-%m-%d')
        cur_end_test_date = (cur_date+ timedelta(days=1)).strftime('%Y-%m-%d')

        test_data = analysis.get_partial_data(cur_start_test_date, cur_end_test_date)
        preprocessed_test_data, preprocessed_test_label = preprocessor.transform(test_data)
        auto_ml.evaluate(preprocessed_test_data, preprocessed_test_label)
        test_result = auto_ml.test_result['LSTM']['test_prediction']

        test_result = preprocessor.inverse_transform_labels(test_result)
        test_result = [int(i) for i in test_result]
        start_index_test = 0
        for i, (name, truth) in enumerate(preprocessed_test_label.items()):
            test_truth = preprocessor.inverse_transform_labels(np.array(truth))
            num_train = len(test_truth)
            test_truth = np.squeeze(test_truth,axis=-1)
            test_truth = test_truth.tolist()
            test_truth = [int(i) for i in test_truth]

            result['test'][name]['prediction'].extend(test_result[start_index_test:start_index_test + num_train])
            result['test'][name]['truth'].extend(test_truth)
            start_index_test += num_train
        # Move to the next day
        cur_date += timedelta(days=1)
    os.makedirs(f'static/results/{time_series_config.task}', exist_ok=True)
    filename = f'static/results/{time_series_config.task}/predictions for {time_series_config.task}.json'
    with open(filename, 'w') as f:
        json.dump(result, f, indent=4)


    # for model_name in train_result.keys():
    #     train_prediction = train_result[model_name]['train_prediction']
    #     train_prediction = preprocessor.inverse_transform_labels(train_prediction)
    #
    #     test_prediction = test_result[model_name]['test_prediction']
    #     test_prediction = preprocessor.inverse_transform_labels(test_prediction)
    #
    #     num_groups = len(preprocessed_training_label)
    #     fig, axes = plt.subplots(nrows=num_groups, ncols=1, figsize=(10, 5 * num_groups))
    #
    #     # Define the overall date range
    #     start_date = pd.to_datetime(start_date)
    #     end_date = pd.to_datetime(end_date)
    #
    #     # Generate a date range for plotting
    #     date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    #
    #     start_index_train = 0
    #     start_index_test = 0
    #     for i, (name, truth) in enumerate(preprocessed_training_label.items()):
    #         train_truth = preprocessor.inverse_transform_labels(np.array(truth))
    #         test_truth = preprocessor.inverse_transform_labels(np.array(preprocessed_test_label[name]))
    #
    #         num_train = len(train_truth)
    #         num_test = len(test_truth)
    #
    #         current_train_pred = train_prediction[start_index_train:start_index_train+num_train]
    #         current_test_pred = test_prediction[start_index_test:start_index_test+num_test]
    #         start_index_train += num_train
    #         start_index_test += num_test
    #
    #         # Plotting
    #         ax = axes[i]
    #         ax.plot(date_range[:num_train], train_truth, label='Train Truth', color='blue')
    #         ax.plot(date_range[:num_train], current_train_pred, label='Train Prediction', color='red', linestyle='--')
    #         ax.plot(date_range[num_train:num_train + num_test], test_truth, label='Test Truth', color='green')
    #         ax.plot(date_range[num_train:num_train + num_test], current_test_pred, label='Test Prediction',
    #                 color='purple', linestyle='--')
    #
    #         # Formatting the x-axis
    #         ax.xaxis.set_major_locator(MonthLocator())
    #         ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    #         plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    #
    #         ax.set_title(f'Group: {name}')
    #         ax.legend()
    #         ax.set_xlabel('Date')
    #         ax.set_ylabel('Value')
    #     plt.title(f"{model_name}:{test_result[model_name]['test_loss']}")
    #     plt.tight_layout()
    #     plt.savefig(f'{model_name}test.png')
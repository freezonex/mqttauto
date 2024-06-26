import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import acf
import os

class TimeSeriesPlot:
    '''
    You can add more time series analysis in this class to give a better view of overall time series data.
    Currently, it supports time series, auto-correlation and fft.
    '''
    def __init__(self, config, dataframe):
        self.config = config
        self.processed_dataframe = dataframe

        if not os.path.exists(f'static/images/{self.config.task}'):
            os.makedirs(f'static/images/{self.config.task}')

    def plot_time_series(self, groups):
        features = [col for col in self.processed_dataframe.columns if col not in [self.config.group_by]]
        num_groups = len(groups)
        num_features = len(features)
        fig, axes = plt.subplots(nrows=num_groups, ncols=num_features, figsize=(15, num_groups * 4))
        for i, group in enumerate(groups):
            group_data = self.processed_dataframe[self.processed_dataframe[self.config.group_by] == group]
            for j, feature in enumerate(features):
                ax = axes[i, j] if len(features) > 1 else axes[i]
                ax.plot(np.array(list(range(len(group_data)))) + 1, group_data[feature], marker='o', linestyle='-')
                ax.set_title(f'{group} - {feature}')
                ax.set_ylabel('Value')
                ax.set_xlabel(self.config.timestamp_column)
        plt.tight_layout()
        plt.savefig(f'static/images/{self.config.task}/time_series_plots.png')
        plt.close(fig)

    def plot_autocorrelation(self, groups):
        features = [col for col in self.processed_dataframe.columns if
                    col not in [self.config.group_by, self.config.label]]
        num_features = len(features)
        num_groups = len(groups)
        fig, axes = plt.subplots(nrows=num_groups, ncols=num_features, figsize=(15, num_groups * 4))

        # auto correlation
        for i, group in enumerate(groups):
            group_data = self.processed_dataframe[self.processed_dataframe[self.config.group_by] == group]
            for j, feature in enumerate(features):
                ax = axes[i, j] if len(features) > 1 else axes[i]
                feature_data = group_data[feature].dropna()
                lag_acf = acf(feature_data, nlags=10)
                ax.stem(range(len(lag_acf)), lag_acf, basefmt="b-", use_line_collection=True)
                ax.set_title(f'{group} - {feature} Autocorrelation')
                ax.set_ylabel('Autocorrelation')
                ax.set_xlabel('Lags')
        plt.tight_layout()
        plt.savefig(f'static/images/{self.config.task}/autocorrelation_plots.png')
        plt.close(fig)

    def plot_fft(self, groups):
        features = [col for col in self.processed_dataframe.columns if
                    col not in [self.config.group_by, self.config.label]]
        num_features = len(features)
        num_groups = len(groups)
        fig, axes = plt.subplots(nrows=len(groups), ncols=num_features, figsize=(15, num_groups * 4))

        for i, group in enumerate(groups):
            group_data = self.processed_dataframe[self.processed_dataframe[self.config.group_by] == group]
            for j, feature in enumerate(features):
                ax = axes[i, j] if num_features > 1 else axes[i]
                data = group_data[feature].dropna()
                fft_values = np.fft.fft(data)
                frequencies = np.fft.fftfreq(len(fft_values))
                # 仅绘制正频率
                mask = frequencies > 0
                frequencies = frequencies[mask]
                power = np.abs(fft_values)[mask]
                ax.plot(frequencies, power)
                ax.set_title(f'{group} - {feature} FFT Analysis')
                ax.set_xlabel('Frequency')
                ax.set_ylabel('Power')
        plt.tight_layout()
        plt.savefig(f'static/images/{self.config.task}/fft_plots.png')
        plt.close(fig)

    def analyze_data(self):
        groups = self.processed_dataframe[self.config.group_by].unique()

        self.plot_time_series(groups)
        self.plot_autocorrelation(groups)
        self.plot_fft(groups)


def plot_grouped_time_series(preprocessed_training_label, preprocessed_test_label, train_prediction, test_prediction):
    num_groups = len(preprocessed_training_label)
    fig, axes = plt.subplots(nrows=num_groups, ncols=2, figsize=(14, num_groups * 5), sharex='col')

    # Flatten axes array for easy iteration if there's more than one row
    if num_groups > 1:
        axes = axes.flatten()
    else:
        axes = [axes]  # Wrap it in a list to use in a loop

    train_pred_index = 0
    test_pred_index = 0

    for i, (name, train_label) in enumerate(preprocessed_training_label.items()):
        test_label = preprocessed_test_label[name]

        # Calculate the lengths of the current group's labels
        train_len = len(train_label)
        test_len = len(test_label)

        # Slicing predictions according to the length of the current group's labels
        current_train_pred = train_prediction[train_pred_index:train_pred_index + train_len]
        current_test_pred = test_prediction[test_pred_index:test_pred_index + test_len]

        # Update indices for next iteration
        train_pred_index += train_len
        test_pred_index += test_len

        # Plot training data
        ax = axes[2 * i]  # Even index for train data
        ax.plot(train_label, label='Train Labels', color='blue')
        ax.plot(current_train_pred, label='Train Predictions', color='red', linestyle='--')
        ax.set_title(f'Training Data - {name}')
        ax.legend()

        # Plot testing data
        ax = axes[2 * i + 1]  # Odd index for test data
        ax.plot(test_label, label='Test Labels', color='blue')
        ax.plot(current_test_pred, label='Test Predictions', color='red', linestyle='--')
        ax.set_title(f'Testing Data - {name}')
        ax.legend()

    plt.tight_layout()
    plt.savefig('test.png')
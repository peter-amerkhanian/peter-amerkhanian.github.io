import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
import statsmodels
from io import StringIO
from collections.abc import Iterable
import matplotlib
from typing import Tuple, Union

def mean_diff(x, y):
    return np.mean(x) - np.mean(y)

def block_bootstrap(ts1, ts2, block_size, n_bootstraps, tests=1):
    n = len(ts1)
    observed_diff = mean_diff(ts1, ts2)
    bootstrap_diffs = np.zeros(n_bootstraps)

    for i in range(n_bootstraps):
        # Generate block indices
        blocks = np.random.choice(range(n - block_size + 1), size=(n // block_size), replace=True)
        ts1_resampled = np.concatenate([ts1[j:j + block_size] for j in blocks])
        ts2_resampled = np.concatenate([ts2[j:j + block_size] for j in blocks])
        # If necessary, trim the resampled data to the original length
        ts1_resampled = ts1_resampled[:n]
        ts2_resampled = ts2_resampled[:n]
        bootstrap_diffs[i] = mean_diff(ts1_resampled, ts2_resampled)
    # Calculate the confidence interval
    # p = 5 / tests
    # ci_lower = np.percentile(bootstrap_diffs, p/2)
    # ci_upper = np.percentile(bootstrap_diffs, 100-p/2)
    return observed_diff, bootstrap_diffs


def table_to_pandas(table, fix_cols=True):
    html_stream = StringIO(table.as_html())
    df = pd.read_html(html_stream)[0]
    if fix_cols:
        column_names = df.iloc[0, :].fillna("")
        df.columns = column_names
        df = df.iloc[1:, :]
    for column in df.columns:
        try:
            df[column] = df[column].astype(float)
        except ValueError:
            # Skip conversion if it fails
            pass
    return df

def custom_legend(ax: matplotlib.axes.Axes,
                  outside_loc: str = None,
                  order: Union[str, list] = "default",
                  title: str = "",
                  linewidth: int = 2,
                  **kwargs) -> matplotlib.axes.Axes:
    """
    Customize the legend location and order on a Matplotlib axis.

    This function adjusts the position of the legend, optionally placing it outside the plot area,
    and can reorder the legend entries based on specified criteria.

    Args:
        ax (matplotlib.axes.Axes): An existing Matplotlib axis object to which the legend belongs.
        outside_loc (str, optional): Specifies the location of the legend outside the plot area.
                                     Must be one of ["lower", "center", "upper", None]. 
                                     Defaults to None.
        order (str, optional): Determines the order of the legend entries. 
                               Must be one of ["default", "reverse", "desc"]. 
                               "default" keeps the current order, 
                               "reverse" reverses the current order, 
                               "desc" orders entries by descending values. 
                               Defaults to "default".

    Returns:
        matplotlib.axes.Axes: The axis object with the customized legend.

    Raises:
        AssertionError: If `outside_loc` is not in ["lower", "center", "upper", None].
    """
    handles, labels = ax.get_legend_handles_labels()
    if order == 'default':
        pass
    elif order == 'reverse':
        handles = handles[::-1]
        labels = labels[::-1]
    elif order == 'desc':
        ordering = np.flip(np.argsort(np.array([line.get_ydata()[-1] for line in ax.lines if len(line.get_ydata())>0])))
        handles = np.array(handles)[ordering].tolist()
        labels = np.array(labels)[ordering].tolist()
    elif isinstance(order, Iterable):
        value_to_index = {value: idx for idx, value in enumerate(labels)}
        indices = [value_to_index[value] for value in order]
        labels = list(order)
        handles = np.array(handles)[indices].tolist()
    else:
        raise Exception("Invalid Order")
    error_msg = "legend_to_right loc must be None or in 'lower', 'center', or 'upper'"
    assert outside_loc in ["lower", "center", "upper", None], error_msg
    if outside_loc == "lower":
        ax.legend(handles, labels, loc='lower left', bbox_to_anchor=(1, 0), **kwargs)
    elif outside_loc == "center":
        ax.legend(handles, labels, loc='center left', bbox_to_anchor=(1, .5), **kwargs)
    elif outside_loc == "upper":
        ax.legend(handles, labels, loc='upper left', bbox_to_anchor=(1, 1), **kwargs)
    else:
        ax.legend(handles, labels, **kwargs)
    legend = ax.get_legend()
    legend.set_title(title)
    for line in legend.get_lines():
        line.set_linewidth(linewidth)
    return ax
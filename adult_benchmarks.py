import os,sys
import numpy as np
from two_naive_bayes import *
from zafar_classifier import *
from prepare_adult_data import *
from prejudice_regularizer import *
from black_box_auditing import *
sys.path.insert(0, "/data/adult/")
from load_adult import *
sys.path.insert(0, 'zafar_fair_classification/') # the code for fair classification is in this directory
import utils as ut
import loss_funcs as lf # loss funcs that can be optimized subject to various constraints



def test_adult_data():

    #Variables for whole functions
    sensitive_attrs = ["sex"]
    sensitive_attr = sensitive_attrs[0]
    train_fold_size = 0.7


    ##############################################################################################################################################
    """
    If need be Repair data using BlackBoxAudit
    """
    ##############################################################################################################################################

    run_adult_repair()

    ##############################################################################################################################################
    """
    Load and Split Data
    """
    ##############################################################################################################################################

    """ Load the adult data """
    print "\n"
    X, y, x_control = load_adult_data("data/adult/adult.csv", load_data_size=16281)
    X_repaired_8, y_repaired_8, x_control_repaired_8 = load_adult_data("data/adult/repaired_adult_.8.csv", load_data_size=16281)
    X_repaired_9, y_repaired_9, x_control_repaired_9 = load_adult_data("data/adult/repaired_adult_.9.csv", load_data_size=16281)
    X_repaired_1, y_repaired_1, x_control_repaired_1 = load_adult_data("data/adult/repaired_adult_1.csv", load_data_size=16281)


    X = ut.add_intercept(X) # add intercept to X before applying the linear classifier
    X_repaired_8 = ut.add_intercept(X)
    X_repaired_9 = ut.add_intercept(X)
    X_repaired_1 = ut.add_intercept(X)


    # shuffle the data
    perm = range(0,len(y)) # shuffle the data before creating each fold
    shuffle(perm)
    X = X[perm]
    X_repaired_8 = X_repaired_8[perm]
    X_repaired_9 = X_repaired_9[perm]
    X_repaired_1 = X_repaired_1[perm]

    y = y[perm]

    print type(x_control["sex"])

    for k in x_control.keys():
        x_control[k] = x_control[k][perm]


    """ Split the data into train and test """

    x_train, y_train, x_control_train, x_test, y_test, x_control_test = ut.split_into_train_test(X, y, x_control, train_fold_size)
    x_train_repaired_8, y_train_repaired_8, x_control_train_repaired_8, x_test_repaired_8, y_test_repaired_8, x_control_test_repaired_8 = ut.split_into_train_test(X_repaired_8, y_repaired_8, x_control_repaired_8, train_fold_size)
    x_train_repaired_9, y_train_repaired_9, x_control_train_repaired_9, x_test_repaired_9, y_test_repaired_9, x_control_test_repaired_9 = ut.split_into_train_test(X_repaired_9, y_repaired_9, x_control_repaired_9, train_fold_size)
    x_train_repaired_1, y_train_repaired_1, x_control_train_repaired_1, x_test_repaired_1, y_test_repaired_1, x_control_test_repaired_1 = ut.split_into_train_test(X_repaired_1, y_repaired_1, x_control_repaired_1, train_fold_size)


    #############################################################################################################################################
    """
    Classify using SVM, logistic regression, and NB on repaired/original data
    """
    ##############################################################################################################################################

    print "\nClassify original and repaired data using SVM/Naive Bayes/Logistic Regression"

    classify_adult("adult_repaired_.8", sensitive_attr, x_train_repaired_8, y_train, x_control_train, x_test_repaired_8, y_test, x_control_test)
    classify_adult("adult_repaired_.9", sensitive_attr, x_train_repaired_8, y_train, x_control_train, x_test_repaired_8, y_test, x_control_test)
    classify_adult("adult_repaired_.1", sensitive_attr, x_train_repaired_8, y_train, x_control_train, x_test_repaired_8, y_test, x_control_test)


    classify_adult("adult_original_data", sensitive_attr, x_train, y_train, x_control_train, x_test, y_test, x_control_test)

    #############################################################################################################################################
    """
    Classify using Kamishima
    """
    ##############################################################################################################################################

    x_train_with_sensitive_feature = []
    for i in range(0, len(x_train)):
        val =  x_control_train["sex"][i]
        feature_array = np.append(x_train[i], val)
        x_train_with_sensitive_feature.append(feature_array)

    x_train_with_sensitive_feature = np.array(x_train_with_sensitive_feature)

    x_test_with_sensitive_feature = []
    for i in range(0, len(x_test)):
        val =  x_control_test["sex"][i]
        feature_array = np.append(x_test[i], val)
        x_test_with_sensitive_feature.append(feature_array)

    x_test_with_sensitive_feature = np.array(x_test_with_sensitive_feature)


    print "\n== Kamishima's Prejudice Reducer Regularizer with fairness param of 30 and 1"

    y_classified_results = train_classify(sensitive_attr, "adult", x_train_with_sensitive_feature, y_train, x_test_with_sensitive_feature, y_test, 1, 30, x_control_test)
    y_classified_results = train_classify(sensitive_attr, "adult", x_train_with_sensitive_feature, y_train, x_test_with_sensitive_feature, y_test, 1, 0, x_control_test)


    ##############################################################################################################################################
    """
    Classify using Calder's Two Naive Bayes
    """
    ##############################################################################################################################################
    run_two_naive_bayes("adult_two_naive_bayes", x_train, y_train, x_control_train, x_test, y_test, x_control_test, sensitive_attr)
    print "\n== Calder's Two Naive Bayes =="

    ##############################################################################################################################################
    """
    Zafar Code
    """
    ##############################################################################################################################################
    #Variables for Zafar classifiers
    apply_fairness_constraints = None
    apply_accuracy_constraint = None
    sep_constraint = None
    loss_function = lf._logistic_loss
    sensitive_attrs_to_cov_thresh = {}
    gamma = None

    """ Classify the data while optimizing for accuracy """
    print "\n== Zafar: Unconstrained (original) classifier =="
    # all constraint flags are set to 0 since we want to train an unconstrained (original) classifier
    apply_fairness_constraints = 0
    apply_accuracy_constraint = 0
    sep_constraint = 0
    w_uncons = train_test_classifier("adult_unconstrained", x_train, y_train, x_control_train, x_test, y_test, x_control_test, loss_function, apply_fairness_constraints, apply_accuracy_constraint, sep_constraint, sensitive_attrs, sensitive_attrs_to_cov_thresh, gamma)

    """ Now classify such that we optimize for accuracy while achieving perfect fairness """
    apply_fairness_constraints = 1 # set this flag to one since we want to optimize accuracy subject to fairness constraints
    apply_accuracy_constraint = 0
    sep_constraint = 0
    sensitive_attrs_to_cov_thresh = {"sex":0}
    print "\n== Zafar:  Classifier with fairness constraint =="
    w_f_cons = train_test_classifier("adult_opt_accuracy", x_train, y_train, x_control_train, x_test, y_test, x_control_test, loss_function, apply_fairness_constraints, apply_accuracy_constraint, sep_constraint, sensitive_attrs, sensitive_attrs_to_cov_thresh, gamma)

    """ Classify such that we optimize for fairness subject to a certain loss in accuracy """
    apply_fairness_constraints = 0 # flag for fairness constraint is set back to0 since we want to apply the accuracy constraint now
    apply_accuracy_constraint = 1 # now, we want to optimize fairness subject to accuracy constraints
    sep_constraint = 0
    gamma = 0.5 # gamma controls how much loss in accuracy we are willing to incur to achieve fairness -- increase gamme to allow more loss in accuracy
    print "\n== Zafar:  Classifier with accuracy constraint =="
    w_a_cons = train_test_classifier("adult_opt_fairness", x_train, y_train, x_control_train, x_test, y_test, x_control_test, loss_function, apply_fairness_constraints, apply_accuracy_constraint, sep_constraint, sensitive_attrs, sensitive_attrs_to_cov_thresh, gamma)

    """
    Classify such that we optimize for fairness subject to a certain loss in accuracy
    In addition, make sure that no points classified as positive by the unconstrained (original) classifier are misclassified.

    """
    apply_fairness_constraints = 0 # flag for fairness constraint is set back to 0 since we want to apply the accuracy constraint now
    apply_accuracy_constraint = 1 # now, we want to optimize accuracy subject to fairness constraints
    sep_constraint = 1 # set the separate constraint flag to one, since in addition to accuracy constrains, we also want no misclassifications for certain points (details in demo README.md)
    gamma = 1000.0
    print "\n== Zafar: Classifier with accuracy constraint (no +ve misclassification) =="
    w_a_cons_fine = train_test_classifier("adult_no_positive_misclassification", x_train, y_train, x_control_train, x_test, y_test, x_control_test, loss_function, apply_fairness_constraints, apply_accuracy_constraint, sep_constraint, sensitive_attrs, sensitive_attrs_to_cov_thresh, gamma)

    ##############################################################################################################################################
    """
    End Zafar Code
    """
    ##############################################################################################################################################


    return

def main():
    test_adult_data()


if __name__ == '__main__':
    main()
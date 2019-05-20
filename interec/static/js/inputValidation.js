/*
* validates the add PR form inputs when the 'Submit" button clicks.
* */
function validateAddPRForm() {

    var id = $('#id')[0].value;
    var title = $('#title')[0].value;
    var description = $('#description')[0].value;
    var files = $('#files')[0].value;
    var requester = $('#requester_login')[0].value;
    var integrator = $('#integrator_login')[0].value;
    var createdDate = $('#created_date')[0].value;
    var mergedDate = $('#merged_date')[0].value;

    if (id === '' || title === '' || description === '' || files === '' || requester === '' || integrator === '' ||
        createdDate === '' || mergedDate === '') {
        alertify.warning("Please fill all the required fields!");
        return false;
    }

    var numberRegex = new RegExp('^\\d+$');
    if (!numberRegex.test(id)) {
        alertify.error("Id should contain only numbers!");
        return false;
    }

    var lettersWithNoSpaceRegex = new RegExp('^[a-zA-Z]+$');
    if (!lettersWithNoSpaceRegex.test(requester)) {
        alertify.error("Requester User Name should contain only letters!");
        return false;
    }

    var returnFlag = false;
    $.ajax({
        url: 'http://localhost:5000/check_pr_id',
        dataType: 'json',
        contentType: 'application/json',
        type: 'POST',
        async: false,
        data: JSON.stringify({id: id}),
        success: function (data) {
            if (data.availability) {
                alertify.error("Entered PR Id is already in the database!");
                returnFlag = false;
            } else {
                returnFlag = true;
            }
        },
        error: function (XHR, status, response) {
            console.log(XHR.response);
            console.log(status);
            console.log(response);
            alertify.error("Internal error occurred!");
            returnFlag = false;
        }
    });
    return returnFlag;
}


/*
* validates the set weight form inputs when the 'Submit" button clicks.
* */
function validateSetWeightsForm() {
    var alpha = $('#alpha')[0].value;
    var beta = $('#beta')[0].value;
    var gamma = $('#gamma')[0].value;

    if (alpha === '' || beta === '' || gamma === '') {
        alertify.warning("Please fill all the required fields!");
        return false;
    }

    var fractionNumberRegex = new RegExp('^0(\\.[1-8])?$');
    if (!fractionNumberRegex.test(alpha)) {
        alertify.error("Alpha should be one of the 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8!");
        return false;
    }

    if (!fractionNumberRegex.test(beta)) {
        alertify.error("Beta should be one of the 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8!");
        return false;
    }

    if (!fractionNumberRegex.test(gamma)) {
        alertify.error("Gamma should be one of the 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8!");
        return false;
    }

    if (parseFloat(alpha) + parseFloat(beta) + parseFloat(gamma) !== parseFloat('1.0')) {
        alertify.error("Alpha + Beta + Gamma should be equal to 1!");
        return false;
    }
}


/*
* validates the get weight form(without file name provided) inputs when the 'Submit" button clicks.
* */
function validateGetWeightsForm1() {
    var offset = $('#offset1')[0].value;
    var limit = $('#limit1')[0].value;

    if (offset === '' || limit === '') {
        alertify.warning("Please fill all the required fields!");
        return false;
    }

    var numberRegex = new RegExp('^\\d+$');
    if (!numberRegex.test(offset)) {
        alertify.error("Offset should contain only numbers!");
        return false;
    }

    if (!numberRegex.test(limit)) {
        alertify.error("Limit should contain only numbers!");
        return false;
    }

    if (parseInt(limit) === 0) {
        alertify.error("Limit must be more than 0!");
        return false;
    }

    var returnFlag = false;
    var pr_count = 0;
    $.ajax({
        url: 'http://localhost:5000/get_pr_count',
        type: 'POST',
        async: false,
        success: function (data) {
            if (data.count) {
                pr_count = data.count;
                if(parseInt(offset)> pr_count) {
                    alertify.error("Offset should be less than PR count!");
                } else {
                    returnFlag = true;
                }
            } else {
                alertify.error("Error occurred while getting PR count!");
                returnFlag = false;
            }
        },
        error: function (XHR, status, response) {
            console.log(XHR.response);
            console.log(status);
            console.log(response);
            alertify.error("Internal error occurred!");
            returnFlag = false;
        }
    });
    return returnFlag;
}


/*
* validates the get weight form(with file name provided) inputs when the 'Submit" button clicks.
* */
function validateGetWeightsForm2() {
    var offset = $('#offset2')[0].value;
    var limit = $('#limit2')[0].value;
    var filename = ($('#file_name')[0].value).toLowerCase();

    if (filename.match(/\.[0-9a-z]+$/i) === null || filename.match(/\.[0-9a-z]+$/i)[0] !== '.csv') {
        alertify.error("The file should be a CSV file!");
        return false;
    }

    if (offset === '' || limit === '') {
        alertify.warning("Please fill all the required fields!");
        return false;
    }

    var numberRegex = new RegExp('^\\d+$');
    if (!numberRegex.test(offset)) {
        alertify.error("Offset should contain only numbers!");
        return false;
    }

    if (!numberRegex.test(limit)) {
        alertify.error("Limit should contain only numbers!");
        return false;
    }

    if (parseInt(limit) === 0) {
        alertify.error("Limit must be more than 0!");
        return false;
    }

    var returnFlag = false;
    var pr_count = 0;
    $.ajax({
        url: 'http://localhost:5000/get_pr_count',
        type: 'POST',
        async: false,
        success: function (data) {
            if (data.count) {
                pr_count = data.count;
                if(parseInt(offset)> pr_count) {
                    alertify.error("Offset should be less than PR count!");
                } else {
                    returnFlag = true;
                }
            } else {
                alertify.error("Error occurred while getting PR count!");
            }
        },
        error: function (XHR, status, response) {
            console.log(XHR.response);
            console.log(status);
            console.log(response);
            alertify.error("Internal error occurred!");
            returnFlag = false;
        }
    });
    return returnFlag;
}


/*
* validates the find integrators for PR form (with all details of the PR) inputs when the 'Submit" button clicks.
* */
function validateFindIntegratorsForm1() {

    var id = $('#id')[0].value;
    var title = $('#title')[0].value;
    var description = $('#description')[0].value;
    var files = $('#files')[0].value;
    var requester = $('#requester_login')[0].value;
    var createdDate = $('#created_date')[0].value;

    if (id === '' || title === '' || description === '' || files === '' || requester === '' || createdDate === '') {
        alertify.warning("Please fill all the required fields!");
        return false;
    }

    var numberRegex = new RegExp('^\\d+$');
    if (!numberRegex.test(id)) {
        alertify.error("Id should contain only numbers!");
        return false;
    }

    var lettersWithNoSpaceRegex = new RegExp('^[a-zA-Z]+$');
    if (!lettersWithNoSpaceRegex.test(requester)) {
        alertify.error("Requester User Name should contain only letters!");
        return false;
    }

    return true;
}


/*
* validates the find integrators for PR form (only by PR id) inputs when the 'Submit" button clicks.
* */
function validateFindIntegratorsForm2() {

    var id = $('#prId')[0].value;

    if (id === '') {
        alertify.warning("Please fill all the required field!");
        return false;
    }

    var numberRegex = new RegExp('^\\d+$');
    if (!numberRegex.test(id)) {
        alertify.error("Id should contain only numbers!");
        return false;
    }

    var returnFlag = false;
    $.ajax({
        url: 'http://localhost:5000/check_pr_id',
        dataType: 'json',
        contentType: 'application/json',
        type: 'POST',
        async: false,
        data: JSON.stringify({id: id}),
        success: function (data) {
            if (!data.availability) {
                alertify.error("Entered PR Id is not found in the database!");
                returnFlag = false;
            } else {
                returnFlag = true;
            }
        },
        error: function (XHR, status, response) {
            console.log(XHR.response);
            console.log(status);
            console.log(response);
            alertify.error("Internal error occurred!");
            returnFlag = false;
        }
    });
    return returnFlag;
}
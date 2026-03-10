function demo2_plot_raw_data(arduinoObj, frequency, UIAxes)

    % SETUP EIDORS
    %addpath(genpath('C:\Users\imaan\Downloads\eidors-v3.12-ng\eidors'));
    %run('C:\Users\imaan\Downloads\eidors-v3.12-ng\eidors-v3.12-ng\eidors\startup.m');

    %numElectrodes = 16; 
    %imdl = mk_common_model('b2d1c', numElectrodes);
    %sim_img = mk_image(imdl.fwd_model, 1);
    %stim = mk_stim_patterns(numElectrodes, 1, '{op}', '{ad}', {}, 1);
    %sim_img.fwd_model.stimulation = stim;

    %imdl.hyperparameter.value = 0.1;
    %imdl.RtR_prior = 'prior_laplace';

    % communication
    if isempty(arduinoObj) || ~isvalid(arduinoObj)
        error('Arduino connection is invalid.');
    end

    % Send frequency
    writeline(arduinoObj, sprintf("F:%d", frequency));
    disp(['Frequency sent: ', num2str(frequency)]);

    % Start streaming
    writeline(arduinoObj, "y"); 
    pause(1);
    baselineStr = readline(arduinoObj);
    baseline = str2num(baselineStr);

    dataStr = readline(arduinoObj);
    accumulatedData = str2num(dataStr);
    numFrames = 3000;

    % Plotting loop
    flush(arduinoObj);
    for i = 1:numFrames
        flush(arduinoObj);
        dataStr = readline(arduinoObj);
        data = str2num(dataStr);

       if ~isempty(data)
            accumulatedData = [accumulatedData; data];
            if i > 1
                cla(UIAxes);
                plot(UIAxes, accumulatedData);
                xlim(UIAxes, [max([1, i-50]) max([i 50])]);
                title(UIAxes, sprintf("Live Frame %d", i));
                drawnow;
            end
        end
    end

    disp("Plotting complete.");
end

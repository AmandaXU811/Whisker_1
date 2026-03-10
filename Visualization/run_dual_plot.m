function run_dual_plot(ax1, ax2, do_record, name_tag)

if nargin < 3 || isempty(do_record)
    do_record = true;
end
if nargin < 4
    name_tag = "";
end
name_tag = string(name_tag);

epath = readlines("EIDORSpath.txt");
comport = strtrim(readlines("COMdetails.txt"));
addpath(genpath(epath));
run(epath + "\startup.m");
disp("run_dual_plot: MATLAB pwd = " + pwd);

%% ---------------- EIDORS MODEL ----------------
imdl = mk_common_model('d2d1c',16);
sim_img = mk_image(imdl.fwd_model,1);
stim = mk_stim_patterns(16, 1, '{ad}', '{ad}', {}, 1);
sim_img.fwd_model.stimulation = stim;

imdl.hyperparameter.value = 0.1;
imdl.RtR_prior = 'prior_laplace';

%% ---------------- SERIAL SETUP ----------------
clear device
device = serialport(comport,115200);
device.Timeout = 0.2; % short timeout to allow stop flag polling
writeline(device,"y");
disp("run_dual_plot: Serial opened on " + comport);

%% ---------------- BASELINE ----------------
dataLine = readline(device);
baseline = str2num(dataLine); %#ok<ST2NM>

if isempty(baseline)
    clear device
    error("Baseline read failed.");
end
disp("run_dual_plot: Baseline length = " + numel(baseline));

numCh = numel(baseline);

%% ---------------- RECORDING CONFIG ----------------
n = 300;
accumulateddata = nan(n, numCh);
t = nan(n,1);

outDir = fullfile(pwd, "recordings");
if do_record
    if ~exist(outDir,"dir"); mkdir(outDir); end
    disp("run_dual_plot: recordings dir = " + outDir);
else
    disp("run_dual_plot: recording disabled.");
end

stopFlag = fullfile(pwd, "stop_recording.flag");

ts = datestr(now,'yyyymmdd_HHMMSS');
if strlength(name_tag) > 0
    csvRawPath   = fullfile(outDir, "eit_raw_"   + name_tag + ".csv");
    csvDeltaPath = fullfile(outDir, "eit_delta_" + name_tag + ".csv");
    csvBasePath  = fullfile(outDir, "eit_baseline_" + name_tag + ".csv");
    matPath      = fullfile(outDir, "eit_full_"  + name_tag + ".mat");
else
    csvRawPath   = fullfile(outDir, "eit_raw_"   + ts + ".csv");
    csvDeltaPath = fullfile(outDir, "eit_delta_" + ts + ".csv");
    csvBasePath  = fullfile(outDir, "eit_baseline_" + ts + ".csv");
    matPath      = fullfile(outDir, "eit_full_"  + ts + ".mat");
end

disp("Recording started...");
t0 = tic;

% (warm-up removed)

%% ---------------- ACQUISITION LOOP ----------------
try
    for i = 1:n
        if exist(stopFlag, "file")
            disp("run_dual_plot: stop flag detected, ending recording.");
            break
        end

        flush(device);
        if device.NumBytesAvailable == 0
            pause(0.01);
            continue
        end
        try
            dataLine = readline(device);
        catch
            continue
        end
        data = str2num(dataLine); %#ok<ST2NM>

        if isempty(data) || numel(data)~=numCh
            continue
        end

        accumulateddata(i,:) = data;
        t(i) = toc(t0);

        %% --- Reconstruction ---
        rec_img = inv_solve(imdl, fliplr(baseline).', fliplr(data).');
        tempFig = figure('Visible','off');
        rec_img.calc_colours.clim = 0.2;
        show_fem(rec_img,[1 0 0]);

        srcAxes = gca;
        cla(ax1);
        copyobj(allchild(srcAxes),ax1);
        close(tempFig);
        ax1.DataAspectRatio = [1 1 1];

        %% --- Raw Plot ---
        plot(ax2, data(data~=0),'b');
        ylim(ax2,[0 2]);
        title(ax2,sprintf('Frame %d',i));
        drawnow;

    end

catch ME
    disp("run_dual_plot: Acquisition interrupted.");
    disp("run_dual_plot: " + ME.message);
    disp("⚠ Acquisition interrupted.");
end

clear device

%% ---------------- CLEAN & SAVE ----------------
validRows = ~all(isnan(accumulateddata),2);
accumulateddata = accumulateddata(validRows,:);
t = t(validRows);

delta = accumulateddata - baseline;

if ~do_record
    disp("run_dual_plot: recording disabled, no files saved.");
    return
end

    % Save CSV
    writematrix(accumulateddata, csvRawPath);
    writematrix(delta, csvDeltaPath);
    writematrix(baseline, csvBasePath);

% Save MAT (完整信息)
meta = struct();
meta.comport = comport;
meta.numFrames = size(accumulateddata,1);
meta.numChannels = numCh;
meta.duration_sec = max(t);
meta.timestamp = ts;
meta.hyper = imdl.hyperparameter.value;
meta.prior = imdl.RtR_prior;

save(matPath, ...
    "accumulateddata", ...
    "delta", ...
    "baseline", ...
    "t", ...
    "meta");

disp("✔ Recording saved.");
disp("Frames recorded: " + meta.numFrames);
disp("Duration (s): " + meta.duration_sec);

end

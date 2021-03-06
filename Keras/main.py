import keras
from keras.models import Sequential
from keras.layers import Dense, Activation,Dropout,LSTM,TimeDistributed
from keras import losses
from keras import optimizers
import numpy as np
from keras.utils import plot_model
from keras.models import load_model
import matplotlib.pyplot as plt
from keras.callbacks import EarlyStopping,ModelCheckpoint
import sys
import re
import subprocess


def transformerArrayEn2D(nomFichier):
	donnees = open(nomFichier,"r")
	lines = donnees.readlines()
	i=0
	data = [[0 for x in range(4)] for y in range(1000)]
	for line in lines:
		s = re.findall(r"[-+]?\d*\.\d+|\d+\t\n\r\f\v", line)
		data[i][0]=float(s[0])
		data[i][1]=float(s[1])
		data[i][2]=float(s[2])
		data[i][3]=float(s[3])
		i+=1
	donnees.close()
	return data

def transformerArrayEn3D(nomFichier,dim1,dim2,dim3):
	data = transformerArrayEn2D(nomFichier)
	data = np.reshape(data,(dim1, dim2, dim3))
	X = data[np.mod(np.arange(data.shape[0]),dim2)!=0].reshape(dim1,dim2-1,dim3)
	return X



data = transformerArrayEn2D("data.txt")

#assuming all 4 columns correspond to 1 song
data_dim = 4
#so one song would be 10x4 2D array 
number_of_notes_per_song = 10
nsongs_train = 100
#tunable parameter
batch_size = 40
epochs = 50
learning_rate = 0.001
opt = optimizers.rmsprop(learning_rate)
cout = 'categorical_crossentropy'
nomFichierDuModele = 'modele.h5'
nomFichierDesPoids = 'poids.h5'


x_train = np.reshape(data,(nsongs_train, number_of_notes_per_song, data_dim))
X = transformerArrayEn3D("data.txt",nsongs_train, number_of_notes_per_song, data_dim)
y = x_train[::number_of_notes_per_song].reshape(nsongs_train,data_dim) 

model = Sequential()
model.add(LSTM(32, input_shape=(number_of_notes_per_song-1, data_dim),return_sequences=True))
model.add(Dropout(0.2))
model.add(LSTM(64))
model.add(Dense(data_dim, activation='sigmoid'))
plot_model(model, to_file='modele.png', show_shapes=True, show_layer_names=True)
model.summary()


model.compile(loss=cout, optimizer=opt,metrics=['accuracy'])
  
history = model.fit(X,y,batch_size=batch_size, epochs=epochs)




#courbe de la precision sur les ensembles de donnees d'apprentissage et de validation au cours des iterations d'apprentissage.
#plt.plot(history.history['acc'])
#plt.title('Precision du modele')
#plt.ylabel('Precision')
#plt.xlabel('Iterations')
#plt.legend(['Apprentissage', 'Test'], loc='upper left')
#plt.show()
# courbe de la perte/cout sur les ensembles de donnees d'apprentissage et de validation au cours des iterations d'apprentissage.
plt.plot(history.history['loss'])
#plt.plot(history.history['val_loss'])
plt.title('Cout du modele')
plt.ylabel('Cout')
plt.xlabel('Iterations')
plt.legend(['Apprentissage', 'Test'], loc='upper left')
plt.show()

#obtenir les valeurs des poids par couche (utiliser le logicie HDFView)
model.save_weights(nomFichierDesPoids)

#EVALUATION
loss_and_metrics = model.evaluate(X, y, batch_size=1)
print ("Loss et metrics ",loss_and_metrics)
model.save(nomFichierDuModele)






# Chargement du modele stocke dans le fichier pour le reutiliser
model = load_model(nomFichierDuModele)



#PREDICTION
test = transformerArrayEn3D("test.txt",nsongs_train,number_of_notes_per_song,data_dim)
previsions = model.predict(test)
np.savetxt('prediction.txt', previsions, fmt="%f")
subprocess.call("python3 denormalisation.py prediction.txt > prediction1.txt", shell=True)
subprocess.call("python3 denormalisation.py test.txt > test1.txt", shell=True)
open("mon_fichier_sortie.txt","w").write(open("test1.txt").read() + open("prediction1.txt").read())
subprocess.call("python3 creation_midi.py mon_fichier_sortie.txt", shell=True)
subprocess.call("timidity newMusic.mid", shell=True)
#sauvegarder le modele
model.save(nomFichierDuModele)
